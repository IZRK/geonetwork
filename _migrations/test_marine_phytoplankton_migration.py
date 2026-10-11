"""Verify the Marine phytoplankton database EML-GBIF MEF."""

from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile


UUID = "1f7b7000-1cc3-428f-974d-a688398f51e0"
SOURCE = Path("/Users/vids/Downloads") / UUID / UUID
ARCHIVE = Path(__file__).with_name("marine-phytoplankton-database-eml-gbif.mef")
NS = {"gmd": "http://www.isotc211.org/2005/gmd", "gco": "http://www.isotc211.org/2005/gco"}


class MarinePhytoplanktonMigrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(ARCHIVE) as package:
            cls.names = set(package.namelist())
            cls.info = ET.fromstring(package.read(f"{UUID}/info.xml"))
            cls.eml = ET.fromstring(package.read(f"{UUID}/metadata/metadata.xml"))

    def test_record_identity_and_catalogue_settings(self):
        source_info = ET.parse(SOURCE / "info.xml").getroot()
        self.assertEqual("eml-gbif", self.info.findtext("general/schema"))
        self.assertEqual(UUID, self.info.findtext("general/uuid"))
        self.assertEqual(UUID, self.eml.attrib["packageId"])
        self.assertEqual(UUID, self.eml.findtext("dataset/alternateIdentifier"))
        self.assertIsNone(self.info.find("general/localId"))
        self.assertIsNone(self.info.find("general/siteId"))
        self.assertEqual(source_info.findtext("general/createDate"), self.info.findtext("general/createDate"))
        self.assertEqual(
            [(item.get("name"), [(op.get("name"), op.get("groupOwner")) for op in item])
             for item in source_info.findall("privileges/group")],
            [(item.get("name"), [(op.get("name"), op.get("groupOwner")) for op in item])
             for item in self.info.findall("privileges/group")],
        )
        self.assertEqual(
            [item.get("name") for item in source_info.findall("categories/category")],
            [item.get("name") for item in self.info.findall("categories/category")],
        )

    def test_source_content_and_required_role_caveats(self):
        source = ET.parse(SOURCE / "metadata/metadata.xml").getroot()
        title = source.findtext(
            ".//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString", namespaces=NS)
        keywords = [item.text for item in source.findall(
            ".//gmd:descriptiveKeywords//gmd:keyword/gco:CharacterString", NS)]
        self.assertEqual(title, self.eml.findtext("dataset/title"))
        self.assertEqual(keywords, [item.text for item in self.eml.findall("dataset/keywordSet/keyword")])
        self.assertEqual("Marine Biology Station Piran - National Institute of Biology",
                         self.eml.findtext("dataset/creator/organizationName"))
        self.assertEqual("custodian", self.eml.findtext("dataset/associatedParty/role"))
        self.assertEqual("Andreja", self.eml.findtext("dataset/contact/individualName/givenName"))
        self.assertIsNone(self.eml.find("dataset/pubDate"))
        self.assertEqual(
            "No abstract was provided in the source ISO metadata.",
            self.eml.findtext("dataset/abstract/para"),
        )
        self.assertIsNone(self.eml.find("dataset/additionalInfo"))
        self.assertEqual("Services and databases", self.eml.findtext(
            "additionalMetadata/metadata/gbif/hierarchyLevel"))

    def test_geographic_extent_and_no_invented_resources(self):
        geographic = self.eml.find("dataset/coverage/geographicCoverage")
        self.assertEqual("Piran", geographic.findtext("geographicDescription"))
        bounds = geographic.find("boundingCoordinates")
        self.assertEqual(["13.2885", "13.9793", "45.6756", "45.4259"],
                         [bounds.findtext(name) for name in (
                             "westBoundingCoordinate", "eastBoundingCoordinate",
                             "northBoundingCoordinate", "southBoundingCoordinate")])
        self.assertFalse(self.eml.findall("dataset/distribution"))
        self.assertFalse(self.eml.findall("additionalMetadata/metadata/gbif/resourceLogoUrl"))
        self.assertFalse(self.eml.findall("dataset/coverage/taxonomicCoverage"))
        self.assertEqual({"index.csv", "index.html", f"{UUID}/info.xml",
                          f"{UUID}/metadata/metadata.xml"}, self.names)
        self.assertFalse(self.info.findall("public/file"))
        self.assertFalse(self.info.findall("private/file"))


if __name__ == "__main__":
    unittest.main()
