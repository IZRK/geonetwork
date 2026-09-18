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
        rendered = [n.text for n in result.findall(".//span[@class='izrk-taxon-name']")]
        self.assertCountEqual(names, rendered)
        self.assertEqual(2, len(result.findall(".//h3")))

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
        for value in ["Plants observed at the site.", "Family: Rosaceae / Genus: Rosa",
                      "Rosa canina", "Dog rose", "GBIF", "family-1"]:
            self.assertIn(value, text)
        self.assertEqual(3, len(result.findall(".//span[@class='izrk-taxon-name']")))
        self.assertEqual("https://www.gbif.org/species/3002469", result.find(".//a").get("href"))

    def test_empty_placeholder_does_not_create_a_rank(self):
        result = self.render("<taxonomicCoverage><taxonomicClassification/>"
                             "</taxonomicCoverage>")
        self.assertEqual([], result.findall(".//h3"))


if __name__ == "__main__":
    unittest.main()
