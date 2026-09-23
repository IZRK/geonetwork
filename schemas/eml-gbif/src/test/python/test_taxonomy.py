"""Run with SAXON_JAR pointing to the Saxon JAR shipped in GeoNetwork's WAR."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


STYLESHEET = (Path(__file__).resolve().parents[2]
              / "main/plugin/eml-gbif/formatter/taxonomy.xsl")


class TaxonomyTest(unittest.TestCase):
    def render(self, coverage, uuid=""):
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
                  <xsl:with-param name="uuid" select="'{uuid}'"/>
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
        rendered = [n.text for n in result.findall(".//span[@class='izrk-taxon-name']")]
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
        self.assertEqual(3, len(result.findall(".//span[@class='izrk-taxon-name']")))
        self.assertEqual("https://www.gbif.org/species/3002469", result.find(".//a").get("href"))
        family = result.find(".//details[@data-name='Rosaceae']")
        genus = family.find(".//details[@data-name='Rosa']")
        self.assertIn("Rosa canina", "".join(genus.itertext()))

    def test_reference_distinguishes_valeriana_and_valerianella(self):
        result = self.render('''<taxonomicCoverage>
          <taxonomicClassification><taxonRankName>Genus</taxonRankName>
            <taxonRankValue>Valeriana</taxonRankValue></taxonomicClassification>
          <taxonomicClassification><taxonRankName>Species</taxonRankName>
            <taxonRankValue>Valerianella eriocarpa</taxonRankValue></taxonomicClassification>
        </taxonomicCoverage>''', "9f64b6e3-22be-4f17-9cc0-8658c7817867")
        family = result.find(".//details[@data-name='Caprifoliaceae']")
        self.assertIsNotNone(family)
        genus = family.find(".//details[@data-name='Valerianella']")
        self.assertIn("Valerianella eriocarpa", "".join(genus.itertext()))
        self.assertIn("Valeriana", "".join(family.itertext()))
        self.assertEqual(2, len(result.findall(".//span[@class='izrk-taxon-name']")))

    def test_reference_is_record_scoped_and_does_not_guess_for_other_records(self):
        result = self.render('''<taxonomicCoverage><taxonomicClassification>
          <taxonRankName>Species</taxonRankName><taxonRankValue>Valerianella eriocarpa</taxonRankValue>
        </taxonomicClassification></taxonomicCoverage>''', "another-record")
        self.assertNotIn("Caprifoliaceae", "".join(result.itertext()))
        self.assertIn("Unlinked names", "".join(result.itertext()))

    def test_recorded_parents_take_priority_over_reference(self):
        result = self.render('''<taxonomicCoverage><taxonomicClassification>
          <taxonRankName>Family</taxonRankName><taxonRankValue>Recorded family</taxonRankValue>
          <taxonomicClassification><taxonRankName>Genus</taxonRankName>
            <taxonRankValue>Valeriana</taxonRankValue></taxonomicClassification>
        </taxonomicClassification></taxonomicCoverage>''', "9f64b6e3-22be-4f17-9cc0-8658c7817867")
        self.assertNotIn("Caprifoliaceae", "".join(result.itertext()))
        self.assertIn("Valeriana", "".join(result.find(".//details[@data-name='Recorded family']").itertext()))

    def test_explicit_source_identifiers_bypass_name_only_enrichment(self):
        result = self.render('''<taxonomicCoverage><taxonomicClassification>
          <taxonRankName>Genus</taxonRankName><taxonRankValue>Valeriana</taxonRankValue>
          <taxonId provider="Source">source-specific-id</taxonId>
        </taxonomicClassification></taxonomicCoverage>''', "9f64b6e3-22be-4f17-9cc0-8658c7817867")
        self.assertNotIn("Caprifoliaceae", "".join(result.itertext()))
        self.assertIn("source-specific-id", "".join(result.itertext()))

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
