"""Verify the Postojna MEF against its ISO source and the local EML profile."""

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


ROOT = Path(__file__).resolve().parents[1]
UUID = "8306e789-a3e5-40b2-aad4-aa69436a063c"
SOURCE = Path(os.environ.get("POSTOJNA_ISO_SOURCE", "/Users/vids/Downloads")) / UUID
ARCHIVE = ROOT / "_migrations/postojna-minisites-eml-gbif-preserved.mef"
SCHEMA = ROOT / "schemas/eml-gbif/src/main/plugin/eml-gbif/schema/eml.xsd"
INDEX_XSL = ROOT / "schemas/eml-gbif/src/main/plugin/eml-gbif/index-fields/index.xsl"
WEBAPP = ROOT / "web/target/geonetwork/WEB-INF"
NS = {"gmd": "http://www.isotc211.org/2005/gmd",
      "gco": "http://www.isotc211.org/2005/gco"}


def signature(node):
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or "").strip(),
            tuple(signature(child) for child in node))


class PostojnaMigrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(ARCHIVE) as archive:
            cls.members = set(archive.namelist())
            cls.metadata = archive.read(f"{UUID}/metadata/metadata.xml")
            cls.info = archive.read(f"{UUID}/info.xml")
            cls.image = archive.read(f"{UUID}/public/IMG_20180404_103534948.jpg")
            cls.index = archive.read("index.csv").decode("utf-8")
        cls.eml = ET.fromstring(cls.metadata)

    @unittest.skipUnless(SOURCE.exists(), "Original ISO export is required")
    def test_source_content_and_geography_are_preserved(self):
        iso = ET.parse(SOURCE / UUID / "metadata/metadata.xml").getroot()
        source_title = iso.findtext(".//gmd:CI_Citation/gmd:title/gco:CharacterString", namespaces=NS)
        source_abstract = iso.findtext(".//gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString", namespaces=NS)
        keywords = [node.text for node in iso.findall(
            ".//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString", NS)]
        self.assertEqual(source_title, self.eml.findtext("dataset/title"))
        paragraphs = [node.text for node in self.eml.findall("dataset/abstract/para")]
        self.assertEqual(source_abstract.split(), " ".join(paragraphs).split())
        self.assertEqual(keywords, [node.text for node in self.eml.findall("dataset/keywordSet/keyword")])
        self.assertEqual(6, len(keywords))
        self.assertIsNone(self.eml.find("dataset/pubDate"))
        self.assertIn("ISO citation date (creation): 2009-12-04",
                      self.eml.findtext("dataset/additionalInfo/para"))
        source_email = iso.findtext(
            "gmd:contact/gmd:CI_ResponsibleParty/.//gmd:electronicMailAddress/gco:CharacterString",
            namespaces=NS)
        self.assertEqual(source_email, self.eml.findtext(
            "dataset/metadataProvider/electronicMailAddress"))
        self.assertEqual("Magdalena", self.eml.findtext(
            "dataset/metadataProvider/individualName/givenName"))
        self.assertEqual("Aljančič", self.eml.findtext(
            "dataset/metadataProvider/individualName/surName"))
        self.assertIsNone(self.eml.find("dataset/metadataProvider/organizationName"))
        self.assertNotIn(source_email, self.eml.findtext("dataset/additionalInfo/para"))
        bounds = iso.find(".//gmd:EX_GeographicBoundingBox", NS)
        for source_name, target_name in (
            ("westBoundLongitude", "westBoundingCoordinate"),
            ("eastBoundLongitude", "eastBoundingCoordinate"),
            ("northBoundLatitude", "northBoundingCoordinate"),
            ("southBoundLatitude", "southBoundingCoordinate"),
        ):
            self.assertEqual(bounds.findtext(f"gmd:{source_name}/gco:Decimal", namespaces=NS),
                             self.eml.findtext(f"dataset/coverage/geographicCoverage/"
                                               f"boundingCoordinates/{target_name}"))

    @unittest.skipUnless(SOURCE.exists(), "Original ISO export is required")
    def test_access_and_attachment_are_preserved(self):
        original = ET.parse(SOURCE / UUID / "info.xml").getroot()
        converted = ET.fromstring(self.info)
        self.assertEqual("eml-gbif", converted.findtext("general/schema"))
        self.assertEqual(UUID, converted.findtext("general/uuid"))
        self.assertEqual(UUID, self.eml.attrib["packageId"])
        self.assertEqual(original.findtext("general/createDate"),
                         converted.findtext("general/createDate"))
        for section in ("categories", "privileges", "public", "private"):
            self.assertEqual(signature(original.find(section)),
                             signature(converted.find(section)))
        for name in ("localId", "siteId", "siteName"):
            self.assertIsNone(converted.find(f"general/{name}"))
        self.assertEqual(hashlib.sha256((SOURCE / UUID / "public/IMG_20180404_103534948.jpg").read_bytes()).digest(),
                         hashlib.sha256(self.image).digest())
        self.assertEqual("IMG_20180404_103534948.jpg",
                         self.eml.findtext("additionalMetadata/metadata/gbif/resourceLogoUrl"))
        self.assertEqual({"index.csv", "index.html", f"{UUID}/info.xml",
                          f"{UUID}/metadata/metadata.xml",
                          f"{UUID}/public/IMG_20180404_103534948.jpg"}, self.members)
        row = list(csv.DictReader(io.StringIO(self.index), delimiter=";"))[0]
        self.assertEqual("eml-gbif", row["schema"])
        self.assertEqual("", row["id"])

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
    def test_actual_keywords_reach_search_fields(self):
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
