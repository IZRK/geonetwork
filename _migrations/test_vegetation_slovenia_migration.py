"""Verify the Vegetation of Slovenia EML-GBIF MEF and source preservation."""

import hashlib
import os
from pathlib import Path
import unicodedata
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile


UUID = "89ce7bbf-cf1b-4fe8-9ef9-70c817bc3789"
SOURCE = (Path(os.environ["VEGETATION_SLOVENIA_ISO_SOURCE"])
          if os.environ.get("VEGETATION_SLOVENIA_ISO_SOURCE") else None)
SOURCE_AVAILABLE = SOURCE is not None
ARCHIVE = Path(__file__).with_name("vegetation-slovenia-eml-gbif.mef")
NS = {"gmd": "http://www.isotc211.org/2005/gmd",
      "gco": "http://www.isotc211.org/2005/gco"}


def normalized(value):
    return " ".join(value.split())


class VegetationSloveniaMigrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(ARCHIVE) as package:
            cls.names = set(package.namelist())
            cls.info = ET.fromstring(package.read(f"{UUID}/info.xml"))
            cls.eml = ET.fromstring(package.read(f"{UUID}/metadata/metadata.xml"))

    def test_schema_identity_and_no_invented_publication_date(self):
        self.assertEqual("eml-gbif", self.info.findtext("general/schema"))
        self.assertEqual(UUID, self.info.findtext("general/uuid"))
        self.assertEqual(UUID, self.eml.attrib["packageId"])
        self.assertEqual(UUID, self.eml.findtext("dataset/alternateIdentifier"))
        self.assertIsNone(self.info.find("general/localId"))
        self.assertIsNone(self.info.find("general/siteId"))
        self.assertIsNone(self.eml.find("dataset/pubDate"))
        self.assertEqual("Services and databases", self.eml.findtext(
            "additionalMetadata/metadata/gbif/hierarchyLevel"))
        self.assertEqual("BIJH ZRC SAZU", self.eml.findtext("dataset/creator/organizationName"))
        self.assertEqual(["custodian", "custodian"], [item.text for item in
            self.eml.findall("dataset/associatedParty/role")])
        self.assertEqual("Filip", self.eml.findtext("dataset/contact/individualName/givenName"))
        self.assertIn("ISO citation creation date: 2003-01-01", self.eml.findtext(
            "dataset/additionalInfo/para"))

    @unittest.skipUnless(SOURCE_AVAILABLE, "Set VEGETATION_SLOVENIA_ISO_SOURCE to compare source metadata")
    def test_metadata_content_and_access_match_source(self):
        iso = ET.parse(SOURCE / "metadata/metadata.xml").getroot()
        info = ET.parse(SOURCE / "info.xml").getroot()
        source_title = iso.findtext(
            ".//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString", namespaces=NS)
        source_abstract = iso.findtext(
            ".//gmd:identificationInfo//gmd:abstract/gco:CharacterString", namespaces=NS)
        source_keywords = [item.text for item in iso.findall(
            ".//gmd:descriptiveKeywords//gmd:keyword/gco:CharacterString", NS)]
        self.assertEqual(source_title, self.eml.findtext("dataset/title"))
        self.assertEqual(normalized(source_abstract), normalized(" ".join(
            item.text for item in self.eml.findall("dataset/abstract/para"))))
        self.assertEqual(source_keywords, [item.text for item in self.eml.findall(
            "dataset/keywordSet/keyword")])
        self.assertEqual(info.findtext("general/createDate"), self.info.findtext("general/createDate"))
        self.assertEqual([item.attrib["name"] for item in info.findall("categories/category")],
                         [item.attrib["name"] for item in self.info.findall("categories/category")])
        self.assertEqual(
            [(group.attrib["name"], [(op.attrib["name"], op.attrib.get("groupOwner")) for op in group])
             for group in info.findall("privileges/group")],
            [(group.attrib["name"], [(op.attrib["name"], op.attrib.get("groupOwner")) for op in group])
             for group in self.info.findall("privileges/group")])

        source_files = {unicodedata.normalize("NFC", item.attrib["name"])
                        for item in info.findall("public/file")}
        output_files = {unicodedata.normalize("NFC", Path(name).name)
                        for name in self.names if name.startswith(f"{UUID}/public/")}
        self.assertEqual(source_files, output_files)
        source_by_nfc = {unicodedata.normalize("NFC", path.name): path
                         for path in (SOURCE / "public").iterdir() if path.is_file()}
        for manifest in info.findall("public/file"):
            filename = manifest.attrib["name"]
            packaged = next(name for name in self.names
                            if name.startswith(f"{UUID}/public/")
                            and unicodedata.normalize("NFC", Path(name).name)
                            == unicodedata.normalize("NFC", filename))
            with ZipFile(ARCHIVE) as archive:
                self.assertEqual(hashlib.sha256(source_by_nfc[unicodedata.normalize("NFC", filename)].read_bytes()).digest(),
                                 hashlib.sha256(archive.read(packaged)).digest())

    def test_coverage_links_and_browse_images(self):
        geographic = self.eml.find("dataset/coverage/geographicCoverage")
        self.assertEqual("Slovenia", geographic.findtext("geographicDescription"))
        bounds = geographic.find("boundingCoordinates")
        self.assertEqual(["13.3753", "16.6106", "46.8766", "45.4218"],
                         [bounds.findtext(name) for name in (
                             "westBoundingCoordinate", "eastBoundingCoordinate",
                             "northBoundingCoordinate", "southBoundingCoordinate")])
        self.assertEqual("VegSlo_U%C5%A02.JPG", self.eml.findtext(
            "additionalMetadata/metadata/gbif/resourceLogoUrl"))
        self.assertIn("ISO additional browse image: VegSlo_U%C5%A0.JPG",
                      self.eml.findtext("dataset/additionalInfo/para"))

    def test_packaged_files_match_manifest(self):
        manifest_files = {unicodedata.normalize("NFC", item.attrib["name"])
                          for item in self.info.findall("public/file")}
        packaged_files = {unicodedata.normalize("NFC", Path(name).name)
                          for name in self.names if name.startswith(f"{UUID}/public/")}
        self.assertEqual(manifest_files, packaged_files)
        self.assertTrue(manifest_files)

    @unittest.skipUnless(SOURCE_AVAILABLE, "Set VEGETATION_SLOVENIA_ISO_SOURCE to compare source metadata")
    def test_online_resources_match_source(self):
        iso = ET.parse(SOURCE / "metadata/metadata.xml").getroot()
        urls = [item.findtext("gmd:linkage/gmd:URL", namespaces=NS) for item in
                iso.findall(".//gmd:CI_OnlineResource", NS)]
        self.assertEqual(urls, [item.findtext("url") for item in
                                self.eml.findall("dataset/distribution/online")])


if __name__ == "__main__":
    unittest.main()
