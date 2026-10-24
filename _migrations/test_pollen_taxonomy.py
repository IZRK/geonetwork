"""Check that pollen taxonomy migrations preserve the exported record."""

from pathlib import Path
import csv
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from _migrations.build_pollen_taxonomy import METADATA, UUID, build, embed_taxonomy


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).with_name("pollen-eml-gbif.mef")
SCHEMA = (ROOT / "schemas/eml-gbif/src/main/plugin/eml-gbif/schema/eml-gbif-profile.xsd")


def classification(rank: str, name: str) -> ET.Element:
    node = ET.Element("taxonomicClassification")
    ET.SubElement(node, "taxonRankName").text = rank
    ET.SubElement(node, "taxonRankValue").text = name
    return node


class PollenTaxonomyTest(unittest.TestCase):
    def test_committed_package_taxonomy_and_schema(self):
        with ZipFile(PACKAGE) as archive:
            info = ET.fromstring(archive.read(f"{UUID}/info.xml"))
            metadata = archive.read(METADATA)
            root = ET.fromstring(metadata)
        self.assertEqual(UUID, info.findtext("general/uuid"))
        self.assertEqual(UUID, root.get("packageId"))
        general = info.find("general")
        self.assertFalse(any(general.find(name) is not None for name in
                             ("localId", "siteId", "siteName", "rating", "popularity")))
        coverage = root.find("./dataset/coverage/taxonomicCoverage")
        family = next(node for node in coverage.findall("taxonomicClassification")
                      if node.findtext("taxonRankValue") == "Caprifoliaceae")
        self.assertCountEqual(["Valeriana", "Valerianella"],
                              [node.findtext("taxonRankValue") for node in
                               family.findall("taxonomicClassification")])
        valerianella = next(node for node in family.findall("taxonomicClassification")
                            if node.findtext("taxonRankValue") == "Valerianella")
        self.assertEqual("Valerianella eriocarpa", valerianella.findtext(
            "taxonomicClassification/taxonRankValue"))
        with ZipFile(PACKAGE) as archive:
            index = list(csv.DictReader(archive.read("index.csv").decode("utf-8").splitlines(),
                                        delimiter=";"))
            index_html = archive.read("index.html").decode("utf-8")
        self.assertEqual(UUID, index[0]["uuid"])
        self.assertEqual("", index[0]["id"])
        self.assertNotIn("Internal ID", index_html)
        self.assertNotIn("520", index_html)
        with tempfile.TemporaryDirectory() as directory:
            xml = Path(directory) / "metadata.xml"
            xml.write_bytes(metadata)
            subprocess.run(["xmllint", "--noout", "--schema", str(SCHEMA), str(xml)],
                           check=True, capture_output=True, text=True)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        root = ET.Element(
            "{https://eml.ecoinformatics.org/eml-2.2.0}eml",
            packageId=f"https://example.org/catalog#/metadata/{UUID}")
        coverage = ET.SubElement(ET.SubElement(ET.SubElement(root, "dataset"), "coverage"),
                                 "taxonomicCoverage")
        for rank, name in (("Genus", "Valeriana"),
                           ("Species", "Valerianella eriocarpa"), ("Species", "Other plant")):
            coverage.append(classification(rank, name))
        self.metadata = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    def write_relationships(self, rows: str) -> Path:
        relationships = self.path / "relationships.csv"
        relationships.write_text(
            "child_rank,child_name,parent_rank,parent_name,source_reference\n" + rows,
            encoding="utf-8")
        return relationships

    def test_build_nests_only_explicit_links_and_preserves_other_members(self):
        relationships = Path(__file__).with_name("pollen-taxonomy.csv")
        source = self.path / "original.mef"
        output = self.path / "updated.mef"
        with ZipFile(source, "w") as archive:
            archive.comment = b"export comment"
            archive.writestr(
                f"{UUID}/info.xml",
                f"<info><general><uuid>{UUID}</uuid></general></info>".encode())
            archive.writestr(METADATA, self.metadata)
            archive.writestr(f"{UUID}/public/image.jpg", b"image bytes")

        build(source, output, relationships)

        with ZipFile(source) as original, ZipFile(output) as updated:
            self.assertEqual(original.namelist(), updated.namelist())
            self.assertEqual(original.comment, updated.comment)
            for name in original.namelist():
                if name != METADATA:
                    self.assertEqual(original.read(name), updated.read(name))
            root = ET.fromstring(updated.read(METADATA))
        coverage = root.find("./dataset/coverage/taxonomicCoverage")
        self.assertCountEqual(["Caprifoliaceae", "Other plant"],
                              [node.findtext("taxonRankValue") for node in
                               coverage.findall("taxonomicClassification")])
        family = next(node for node in coverage.findall("taxonomicClassification")
                      if node.findtext("taxonRankValue") == "Caprifoliaceae")
        self.assertEqual(["Valeriana", "Valerianella"],
                         [node.findtext("taxonRankValue") for node in
                          family.findall("taxonomicClassification")])
        genus = family.findall("taxonomicClassification")[1]
        self.assertEqual("Valerianella eriocarpa",
                         genus.findtext("taxonomicClassification/taxonRankValue"))

    def test_missing_parent_or_cycle_is_rejected(self):
        missing = self.write_relationships(
            "Genus,Valeriana,Family,Unknown family,source-row-1\n")
        result = ET.fromstring(embed_taxonomy(self.metadata, missing))
        coverage = result.find("./dataset/coverage/taxonomicCoverage")
        unknown_family = next(node for node in coverage.findall("taxonomicClassification")
                              if node.findtext("taxonRankValue") == "Unknown family")
        self.assertEqual("Valeriana", unknown_family.findtext(
            "taxonomicClassification/taxonRankValue"))

        cycle = self.write_relationships(
            "Genus,Valeriana,Family,Caprifoliaceae,source-row-1\n"
            "Family,Caprifoliaceae,Genus,Valeriana,source-row-2\n")
        with self.assertRaisesRegex(ValueError, "cycle"):
            embed_taxonomy(self.metadata, cycle)

    def test_relationships_require_source_references(self):
        relationships = self.write_relationships(
            "Genus,Valeriana,Family,Caprifoliaceae,\n")
        with self.assertRaisesRegex(ValueError, "source reference"):
            embed_taxonomy(self.metadata, relationships)


if __name__ == "__main__":
    unittest.main()
