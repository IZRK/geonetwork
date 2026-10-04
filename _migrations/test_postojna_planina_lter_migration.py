"""Check the Postojna-Planina LTER EML-GBIF MEF import package."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
UUID = "d3011b1e-3aa5-4b61-a3bc-94da67f582c8"
SOURCE = Path("/Users/vids/Downloads") / UUID / UUID
ARCHIVE = Path(__file__).with_name("postojna-planina-lter-eml-gbif.mef")
NS = {"gmd": "http://www.isotc211.org/2005/gmd",
      "gco": "http://www.isotc211.org/2005/gco"}


def normalized(value):
    return " ".join(value.split())


class PostojnaPlaninaLterMigrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(ARCHIVE) as package:
            cls.names = set(package.namelist())
            cls.info = ET.fromstring(package.read(f"{UUID}/info.xml"))
            cls.eml = ET.fromstring(package.read(f"{UUID}/metadata/metadata.xml"))
            cls.public = {
                item.attrib["name"]: package.read(f"{UUID}/public/{item.attrib['name']}")
                for item in cls.info.findall("public/file")
            }

    def test_schema_identity_and_record_semantics(self):
        self.assertEqual("eml-gbif", self.info.findtext("general/schema"))
        self.assertEqual(UUID, self.info.findtext("general/uuid"))
        self.assertEqual(UUID, self.eml.attrib["packageId"])
        self.assertEqual(UUID, self.eml.findtext("dataset/alternateIdentifier"))
        self.assertIsNone(self.info.find("general/localId"))
        self.assertIsNone(self.info.find("general/siteId"))
        self.assertIsNone(self.eml.find("dataset/pubDate"))
        self.assertEqual("Research sites", self.eml.findtext(
            "additionalMetadata/metadata/gbif/hierarchyLevel"))
        self.assertEqual("IZRK ZRC SAZU", self.eml.findtext(
            "dataset/creator/organizationName"))
        self.assertEqual("custodian", self.eml.findtext(
            "dataset/associatedParty/role"))
        self.assertEqual("Magdalena", self.eml.findtext(
            "dataset/contact/individualName/givenName"))
        self.assertEqual("Aljančič", self.eml.findtext(
            "dataset/contact/individualName/surName"))
        self.assertEqual("https://deims.org/b5bcf1f8-b905-4190-bb82-12d0d73904d0",
                         self.eml.findtext("dataset/distribution/online/url"))

    @unittest.skipUnless(SOURCE.exists(), "original extracted MEF is unavailable")
    def test_content_access_and_attachment_hashes_match_source(self):
        iso = ET.parse(SOURCE / "metadata/metadata.xml").getroot()
        info = ET.parse(SOURCE / "info.xml").getroot()
        source_title = iso.findtext(".//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString", namespaces=NS)
        source_abstract = iso.findtext(".//gmd:identificationInfo//gmd:abstract/gco:CharacterString", namespaces=NS)
        source_keywords = [item.text for item in iso.findall(
            ".//gmd:descriptiveKeywords//gmd:keyword/gco:CharacterString", NS)]
        self.assertEqual(source_title, self.eml.findtext("dataset/title"))
        self.assertEqual(normalized(source_abstract), normalized(" ".join(
            item.text for item in self.eml.findall("dataset/abstract/para"))))
        self.assertEqual(source_keywords, [item.text for item in self.eml.findall(
            "dataset/keywordSet/keyword")])
        self.assertEqual(info.findtext("general/createDate"), self.info.findtext("general/createDate"))
        self.assertEqual(
            [item.attrib["name"] for item in info.findall("categories/category")],
            [item.attrib["name"] for item in self.info.findall("categories/category")],
        )
        self.assertEqual(
            [(group.attrib["name"], [operation.attrib["name"] for operation in group])
             for group in info.findall("privileges/group")],
            [(group.attrib["name"], [operation.attrib["name"] for operation in group])
             for group in self.info.findall("privileges/group")],
        )
        source_names = {item.attrib["name"] for item in info.findall("public/file")}
        self.assertEqual(source_names, set(self.public))
        self.assertEqual(source_names, {
            Path(name).name for name in self.names if name.startswith(f"{UUID}/public/")
        })
        for name, payload in self.public.items():
            self.assertEqual(hashlib.sha256((SOURCE / "public" / name).read_bytes()).digest(),
                             hashlib.sha256(payload).digest())
        self.assertIn("index.csv", self.names)
        self.assertIn("index.html", self.names)

    def test_coverage_and_three_browse_images(self):
        self.assertEqual("Postojna", self.eml.findtext(
            "dataset/coverage/geographicCoverage/geographicDescription"))
        bounds = self.eml.find("dataset/coverage/geographicCoverage/boundingCoordinates")
        self.assertEqual(["14.042373940794509", "14.326010845064376",
                          "45.87905342965473", "45.70137906260968"],
                         [bounds.findtext(name) for name in (
                             "westBoundingCoordinate", "eastBoundingCoordinate",
                             "northBoundingCoordinate", "southBoundingCoordinate")])
        self.assertEqual("Zguba%20jama_tp.JPG", self.eml.findtext(
            "additionalMetadata/metadata/gbif/resourceLogoUrl"))
        additional = self.eml.findtext("dataset/additionalInfo/para")
        self.assertIn("ISO additional browse image: Planinska%20jama.JPG", additional)
        self.assertIn("ISO additional browse image: PPCS.JPG", additional)
        self.assertEqual({"Zguba jama_tp.JPG", "Planinska jama.JPG", "PPCS.JPG"},
                         set(self.public))

    def test_all_keywords_are_indexed(self):
        stylesheet = ROOT / "schemas/eml-gbif/src/main/plugin/eml-gbif/index-fields/index.xsl"
        webapp = ROOT / "web/target/geonetwork/WEB-INF"
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "metadata.xml"
            result = Path(temporary) / "index.xml"
            with ZipFile(ARCHIVE) as package:
                source.write_bytes(package.read(f"{UUID}/metadata/metadata.xml"))
            process = subprocess.run(
                ["java", "-cp", f"{webapp / 'classes'}:{webapp / 'lib'}/*",
                 "net.sf.saxon.Transform", f"-s:{source}", f"-xsl:{stylesheet}", f"-o:{result}"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            index = ET.parse(result).getroot()
            expected = [item.text for item in self.eml.findall("dataset/keywordSet/keyword")]
            self.assertEqual(expected, [item["default"] for item in json.loads(index.findtext("tag"))])
            self.assertEqual(len(expected), int(index.findtext("tagNumber")))
            self.assertEqual(expected, [item["default"] for item in
                                        json.loads(index.findtext("allKeywords"))["otherKeywords-theme"]["keywords"]])


if __name__ == "__main__":
    unittest.main()
