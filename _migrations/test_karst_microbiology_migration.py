"""Check the converted MEF against the supplied ISO record and EML profile."""

import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from build_karst_microbiology_eml import UUID


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("KARST_MICROBIOLOGY_ISO_SOURCE",
                             "/Users/vids/Downloads/28b6a390-8254-479b-ba55-c70f59e121d6"))
ARCHIVE = ROOT / "_migrations/karst-microbiological-database-eml-gbif-preserved.mef"
SCHEMA = ROOT / "schemas/eml-gbif/src/main/plugin/eml-gbif/schema/eml.xsd"
INDEX_XSL = ROOT / "schemas/eml-gbif/src/main/plugin/eml-gbif/index-fields/index.xsl"
WEBAPP = ROOT / "web/target/geonetwork/WEB-INF"
NS = {"gmd": "http://www.isotc211.org/2005/gmd",
      "gco": "http://www.isotc211.org/2005/gco"}


def signature(node):
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or "").strip(),
            tuple(signature(child) for child in node))


class KarstMicrobiologyMigrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(ARCHIVE) as archive:
            cls.members = set(archive.namelist())
            cls.metadata = archive.read(f"{UUID}/metadata/metadata.xml")
            cls.info = archive.read(f"{UUID}/info.xml")
            cls.image = archive.read(f"{UUID}/public/20230516_100336.jpg")
            cls.index = archive.read("index.csv").decode("utf-8")
        cls.eml = ET.fromstring(cls.metadata)

    @unittest.skipUnless(SOURCE.exists(), "The supplied ISO export is required")
    def test_source_content_and_geography_are_preserved(self):
        iso = ET.parse(SOURCE / UUID / "metadata/metadata.xml").getroot()
        self.assertEqual(iso.findtext(".//gmd:CI_Citation/gmd:title/gco:CharacterString", namespaces=NS),
                         self.eml.findtext("dataset/title"))
        abstract = iso.findtext(".//gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString",
                                namespaces=NS)
        paragraphs = [node.text for node in self.eml.findall("dataset/abstract/para")]
        self.assertEqual(abstract.split(), " ".join(paragraphs).split())
        keywords = [node.text for node in iso.findall(
            ".//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString", NS)]
        self.assertEqual(keywords, [node.text for node in self.eml.findall("dataset/keywordSet/keyword")])
        self.assertEqual(9, len(keywords))
        self.assertIsNone(self.eml.find("dataset/pubDate"))
        self.assertEqual("eng", self.eml.findtext("dataset/language"))
        self.assertEqual("IZRK ZRC SAZU", self.eml.findtext("dataset/creator/organizationName"))
        self.assertEqual("custodian", self.eml.findtext("dataset/associatedParty/role"))
        self.assertEqual("Janez", self.eml.findtext("dataset/contact/individualName/givenName"))
        self.assertEqual("Mulec", self.eml.findtext("dataset/contact/individualName/surName"))
        self.assertEqual("janez.mulec@zrc-sazu.si",
                         self.eml.findtext("dataset/contact/electronicMailAddress"))
        self.assertEqual("Slovenia", self.eml.findtext(
            "dataset/coverage/geographicCoverage/geographicDescription"))
        bounds = iso.find(".//gmd:EX_GeographicBoundingBox", NS)
        for source_name, target_name in (
            ("westBoundLongitude", "westBoundingCoordinate"),
            ("eastBoundLongitude", "eastBoundingCoordinate"),
            ("northBoundLatitude", "northBoundingCoordinate"),
            ("southBoundLatitude", "southBoundingCoordinate"),
        ):
            self.assertEqual(bounds.findtext(f"gmd:{source_name}/gco:Decimal", namespaces=NS),
                             self.eml.findtext("dataset/coverage/geographicCoverage/"
                                               f"boundingCoordinates/{target_name}"))

    @unittest.skipUnless(SOURCE.exists(), "The supplied ISO export is required")
    def test_mef_access_and_attachment_are_preserved(self):
        original = ET.parse(SOURCE / UUID / "info.xml").getroot()
        converted = ET.fromstring(self.info)
        self.assertEqual("eml-gbif", converted.findtext("general/schema"))
        self.assertEqual(UUID, converted.findtext("general/uuid"))
        self.assertEqual(UUID, self.eml.attrib["packageId"])
        self.assertEqual(UUID, self.eml.findtext("dataset/alternateIdentifier"))
        self.assertEqual(original.findtext("general/createDate"),
                         converted.findtext("general/createDate"))
        for section in ("categories", "privileges", "public", "private"):
            self.assertEqual(signature(original.find(section)),
                             signature(converted.find(section)))
        for name in ("localId", "siteId", "siteName", "rating", "popularity"):
            self.assertIsNone(converted.find(f"general/{name}"))
        image = SOURCE / UUID / "public/20230516_100336.jpg"
        self.assertEqual(hashlib.sha256(image.read_bytes()).digest(),
                         hashlib.sha256(self.image).digest())
        self.assertEqual("20230516_100336.jpg",
                         self.eml.findtext("additionalMetadata/metadata/gbif/resourceLogoUrl"))
        self.assertEqual({"index.csv", "index.html", f"{UUID}/info.xml",
                          f"{UUID}/metadata/metadata.xml", f"{UUID}/public/{image.name}"}, self.members)
        row = list(csv.DictReader(io.StringIO(self.index), delimiter=";"))[0]
        self.assertEqual("eml-gbif", row["schema"])
        self.assertEqual("", row["id"])
        self.assertEqual(self.eml.findtext("dataset/title"), row["title"])

    def test_eml_validates(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "metadata.xml"
            source.write_bytes(self.metadata)
            result = subprocess.run(
                ["xmllint", "--nonet", "--noout", "--schema", str(SCHEMA), str(source)],
                capture_output=True, text=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)

    @unittest.skipUnless((WEBAPP / "lib/saxon-9.1.0.8b-patch.jar").exists(),
                         "GeoNetwork webapp dependencies are required")
    def test_keywords_reach_search_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "metadata.xml"
            output = Path(directory) / "index.xml"
            source.write_bytes(self.metadata)
            result = subprocess.run(
                ["java", "-cp", f"{WEBAPP / 'classes'}:{WEBAPP / 'lib'}/*",
                 "net.sf.saxon.Transform", f"-s:{source}", f"-xsl:{INDEX_XSL}",
                 f"-o:{output}"], capture_output=True, text=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            index = ET.parse(output).getroot()
            keywords = [node.text for node in self.eml.findall("dataset/keywordSet/keyword")]
            self.assertEqual(keywords, [item["default"] for item in json.loads(index.findtext("tag"))])
            self.assertEqual(str(len(keywords)), index.findtext("tagNumber"))
            badges = json.loads(index.findtext("allKeywords"))
            self.assertEqual(keywords, [item["default"] for item in
                                        badges["otherKeywords-theme"]["keywords"]])


if __name__ == "__main__":
    unittest.main()
