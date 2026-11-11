"""Render portal additional information with the Saxon JAR used by GeoNetwork."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree as ET


PORTAL = (Path(__file__).resolve().parents[2]
          / "main/plugin/eml-gbif/formatter/xsl-view/portal.xsl")
EML = "https://eml.ecoinformatics.org/eml-2.2.0"


@unittest.skipUnless(os.environ.get("SAXON_JAR"), "SAXON_JAR is required")
class PortalAdditionalInfoTest(unittest.TestCase):
    def render(self, paragraphs):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            root = ET.Element("root")
            dataset = ET.SubElement(ET.SubElement(root, f"{{{EML}}}eml"), "dataset")
            ET.SubElement(dataset, "title").text = "Example"
            info = ET.SubElement(dataset, "additionalInfo")
            for paragraph in paragraphs:
                ET.SubElement(info, "para").text = paragraph
            ET.ElementTree(root).write(directory / "input.xml", encoding="utf-8")

            stubs = "".join(f'<xsl:template name="{name}"/>' for name in (
                "eml-keywords", "eml-geographic-coverage", "eml-temporal-coverage",
                "eml-distribution", "eml-taxonomic-coverage", "eml-methods"))
            stubs += '''<xsl:template name="render-paragraph-html"><xsl:param name="node"/></xsl:template>
              <xsl:template name="eml-party-table"><xsl:param name="label"/><xsl:param name="nodes"/></xsl:template>
              <xsl:template name="eml-field"><xsl:param name="label"/><xsl:param name="value"/></xsl:template>'''
            (directory / "test.xsl").write_text(f'''<xsl:stylesheet
              xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
              xmlns:eml="{EML}" version="2.0">
              <xsl:include href="{PORTAL.as_uri()}"/>
              <xsl:variable name="metadata" select="/root/eml:eml"/>
              <xsl:variable name="metadataUuid" select="'example'"/>
              <xsl:variable name="nodeUrl" select="''"/>
              <xsl:variable name="source" select="''"/>
              <xsl:variable name="root" select="'div'"/>
              <xsl:variable name="view" select="'portal'"/>
              <xsl:template match="/" priority="3">
                <xsl:call-template name="eml-portal-record"/>
              </xsl:template>
              {stubs}
              <xsl:template name="addLineBreaksAndHyperlinks">
                <xsl:param name="txt"/><xsl:value-of select="$txt"/>
              </xsl:template>
              <xsl:template match="eml:eml" mode="getOverviews"/>
            </xsl:stylesheet>''', encoding="utf-8")
            subprocess.run([
                "java", "-cp", str(Path(os.environ["SAXON_JAR"]).resolve()),
                "net.sf.saxon.Transform", f"-s:{directory / 'input.xml'}",
                f"-xsl:{directory / 'test.xsl'}", f"-o:{directory / 'output.xml'}",
            ], check=True, capture_output=True, text=True)
            return ET.parse(directory / "output.xml").getroot()

    def test_renders_labels_and_prose_but_not_image_markers(self):
        result = self.render(["ISO status: active\nISO additional browse image: figure.jpg",
                              "A public note about the dataset."])
        self.assertEqual(["ISO status"], [node.text for node in result.findall(
            ".//span[@class='izrk-eml-additional-label']")])
        self.assertEqual(["active"], [node.text for node in result.findall(
            ".//span[@class='izrk-eml-additional-value']")])
        self.assertEqual(["A public note about the dataset."], [node.text for node in result.findall(
            ".//p[@class='izrk-eml-additional-note']")])
        self.assertNotIn("figure.jpg", "".join(result.itertext()))

    def test_image_marker_alone_does_not_create_an_empty_section(self):
        result = self.render(["ISO additional browse image: figure.jpg"])
        self.assertFalse(result.findall(".//div[@class='izrk-eml-additional-info']"))


if __name__ == "__main__":
    unittest.main()
