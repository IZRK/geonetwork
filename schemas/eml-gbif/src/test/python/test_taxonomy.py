"""Run with SAXON_JAR pointing to the Saxon JAR shipped in GeoNetwork's WAR."""

import os
from zipfile import ZipFile
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


STYLESHEET = (Path(__file__).resolve().parents[2]
              / "main/plugin/eml-gbif/formatter/taxonomy.xsl")
COPEPODA_MEF = Path(__file__).resolve().parents[5] / "_migrations/copepoda-eml-gbif-preserved.mef"


class TaxonomyTest(unittest.TestCase):
    @staticmethod
    def rendered_taxon_names(result):
        labels = result.findall(".//span[@class='izrk-taxon-name']")
        searches = result.findall(".//a[@class='izrk-taxon-search']")
        return [node.text for node in labels + searches]

    def render(self, coverage):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "input.xml").write_text(coverage)
            (directory / "view.xsl").write_text(f'''<xsl:stylesheet
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0">
              <xsl:include href="{STYLESHEET.as_uri()}"/>
              <xsl:output method="xml"/>
              <xsl:template match="/">
                <result><xsl:call-template name="eml-taxonomy">
                  <xsl:with-param name="coverage" select="//taxonomicCoverage"/>
                </xsl:call-template></result>
              </xsl:template>
            </xsl:stylesheet>''')
            subprocess.run([
                "java", "-cp", os.environ["SAXON_JAR"], "net.sf.saxon.Transform",
                f"-s:{directory / 'input.xml'}", f"-xsl:{directory / 'view.xsl'}",
                f"-o:{directory / 'result.xml'}",
            ], check=True, capture_output=True, text=True)
            return ET.parse(directory / "result.xml").getroot()

    def test_groups_ranks_without_dropping_duplicates_or_names(self):
        names = [f"Taxon {i}" for i in range(165)] + ["Taxon 0"]
        result = self.render("<taxonomicCoverage>" + "".join(
            f"<taxonomicClassification><taxonRankName>{'Genus' if i % 2 else 'Species'}</taxonRankName>"
            f"<taxonRankValue>{name}</taxonRankValue></taxonomicClassification>"
            for i, name in enumerate(names)) + "</taxonomicCoverage>")
        rendered = self.rendered_taxon_names(result)
        self.assertCountEqual(names, rendered)
        self.assertEqual(["Genus", "Species"], [n.text for n in result.findall(".//h5")])
        self.assertIn("166 recorded entries", "".join(result.itertext()))

    def test_preserves_lineage_common_names_and_identifiers(self):
        result = self.render('''<taxonomicCoverage>
          <generalTaxonomicCoverage>Plants observed at the site.</generalTaxonomicCoverage>
          <taxonomicClassification id="family-1">
            <taxonRankName>Family</taxonRankName><taxonRankValue>Rosaceae</taxonRankValue>
            <taxonomicClassification>
              <taxonRankName>Genus</taxonRankName><taxonRankValue>Rosa</taxonRankValue>
              <taxonomicClassification>
                <taxonRankName>Species</taxonRankName><taxonRankValue>Rosa canina</taxonRankValue>
                <commonName>Dog rose</commonName>
                <taxonId provider="GBIF">https://www.gbif.org/species/3002469</taxonId>
              </taxonomicClassification>
            </taxonomicClassification>
          </taxonomicClassification>
        </taxonomicCoverage>''')
        text = "".join(result.itertext())
        for value in ["Plants observed at the site.", "Rosaceae", "Rosa",
                      "Rosa canina", "Dog rose", "GBIF", "family-1"]:
            self.assertIn(value, text)
        self.assertEqual(3, len(self.rendered_taxon_names(result)))
        self.assertIsNotNone(result.find(".//a[@href='https://www.gbif.org/species/3002469']"))
        family = result.find(".//details[@data-name='Rosaceae']")
        genus = family.find(".//details[@data-name='Rosa']")
        self.assertIn("Rosa canina", "".join(genus.itertext()))

    def test_copepoda_hierarchy_comes_from_mef(self):
        with ZipFile(COPEPODA_MEF) as archive:
            metadata = ET.fromstring(archive.read(
                "c7710542-10ea-43e8-b4d7-9bdd3d559905/metadata/metadata.xml"))
        coverage = metadata.find("./dataset/coverage/taxonomicCoverage")
        result = self.render(ET.tostring(coverage, encoding="unicode"))
        branches = result.findall(".//details[@class='izrk-taxon-branch']")
        self.assertCountEqual(["Cyclopoida", "Harpacticoida"],
                              [branch.get("data-name") for branch in branches])
        self.assertEqual(32, len(self.rendered_taxon_names(result)))
        self.assertEqual(30, len(result.findall(".//a[@class='izrk-taxon-search']")))
        self.assertNotIn("Unlinked names", "".join(result.itertext()))
        bryocamptus = result.find(
            ".//a[@href='https://www.gbif.org/taxon/search?q=Bryocamptus+n.sp.+1']")
        self.assertIsNotNone(bryocamptus)

    def test_flat_name_does_not_inherit_an_app_specific_parent(self):
        result = self.render('''<taxonomicCoverage><taxonomicClassification>
          <taxonRankName>Species</taxonRankName><taxonRankValue>Valerianella eriocarpa</taxonRankValue>
        </taxonomicClassification></taxonomicCoverage>''')
        self.assertNotIn("Caprifoliaceae", "".join(result.itertext()))
        self.assertIn("Unlinked names", "".join(result.itertext()))

    def test_homonyms_in_different_families_stay_separate(self):
        result = self.render("<taxonomicCoverage>" + "".join(f'''
          <taxonomicClassification><taxonRankName>Family</taxonRankName><taxonRankValue>{family}</taxonRankValue>
            <taxonomicClassification><taxonRankName>Genus</taxonRankName><taxonRankValue>Same name</taxonRankValue>
              <taxonomicClassification><taxonRankName>Species</taxonRankName><taxonRankValue>{species}</taxonRankValue>
              </taxonomicClassification></taxonomicClassification></taxonomicClassification>'''
          for family, species in [("First family", "First species"), ("Second family", "Second species")]) + "</taxonomicCoverage>")
        first = "".join(result.find(".//details[@data-name='First family']").itertext())
        second = "".join(result.find(".//details[@data-name='Second family']").itertext())
        self.assertIn("First species", first)
        self.assertNotIn("Second species", first)
        self.assertIn("Second species", second)

    def test_unlinked_ranks_are_ordered_without_invented_parents(self):
        result = self.render("<taxonomicCoverage>" + "".join(f'''
          <taxonomicClassification><taxonRankName>{rank}</taxonRankName>
          <taxonRankValue>{rank} name</taxonRankValue></taxonomicClassification>'''
          for rank in ["Species", "Genus", "Family"]) + "</taxonomicCoverage>")
        self.assertEqual(["Family", "Genus", "Species"], [n.text for n in result.findall(".//h5")])
        self.assertEqual([], result.findall(".//details[@class='izrk-taxon-branch']"))

    def test_empty_placeholder_does_not_create_a_rank(self):
        result = self.render("<taxonomicCoverage><taxonomicClassification/>"
                             "</taxonomicCoverage>")
        self.assertEqual([], result.findall(".//details"))


if __name__ == "__main__":
    unittest.main()
