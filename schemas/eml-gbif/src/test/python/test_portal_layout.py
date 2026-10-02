"""Keep the abstract and keywords visible in the EML portal record."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


PORTAL = (Path(__file__).resolve().parents[2]
          / "main/plugin/eml-gbif/formatter/xsl-view/portal.xsl")
VIEW = PORTAL.with_name("view.xsl")
XSL = "{http://www.w3.org/1999/XSL/Transform}"


class PortalLayoutTest(unittest.TestCase):
    def test_portal_renders_abstract_and_keywords_below_image(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / "record.xml"
            source.write_text('''<root xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">
              <eml:eml><dataset><title>Example</title><abstract>
                <para>First paragraph.</para><para>Second paragraph.</para>
              </abstract></dataset></eml:eml></root>''', encoding="utf-8")
            stylesheet = directory / "portal-test.xsl"
            stylesheet.write_text(f'''<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">
              <xsl:include href="{PORTAL.as_uri()}"/>
              <xsl:param name="root" select="'div'"/>
              <xsl:param name="view" select="'portal'"/>
              <xsl:variable name="metadata" select="/root/eml:eml"/>
              <xsl:variable name="metadataUuid" select="'example'"/>
              <xsl:variable name="nodeUrl" select="'https://example.org/'"/>
              <xsl:variable name="source" select="'source'"/>
              <xsl:template name="render-paragraph-html">
                <xsl:param name="node"/>
                <xsl:for-each select="$node/para"><p><xsl:value-of select="."/></p></xsl:for-each>
              </xsl:template>
              <xsl:template name="eml-keywords"><div id="keywords"/></xsl:template>
              <xsl:template name="eml-geographic-coverage"/>
              <xsl:template name="eml-temporal-coverage"/>
              <xsl:template name="eml-distribution"/>
              <xsl:template name="eml-taxonomic-coverage"/>
              <xsl:template name="eml-methods"/>
              <xsl:template name="eml-party-table">
                <xsl:param name="label"/><xsl:param name="nodes"/>
              </xsl:template>
              <xsl:template name="eml-field">
                <xsl:param name="label"/><xsl:param name="value"/>
              </xsl:template>
              <xsl:template match="eml:eml" mode="getOverviews"><img id="overview"/></xsl:template>
            </xsl:stylesheet>''', encoding="utf-8")
            output = directory / "portal.xml"
            process = subprocess.run(
                ["java", "-cp", os.environ["SAXON_JAR"], "net.sf.saxon.Transform",
                 f"-s:{source}", f"-xsl:{stylesheet}", f"-o:{output}"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            record = ET.parse(output).getroot()
            abstract = record.find(".//section[@class='izrk-eml-abstract']")
            self.assertEqual(["First paragraph.", "Second paragraph."],
                             [p.text for p in abstract.findall("p")])
            header = record.find(".//div[@class='row izrk-record-header gn-card gn-card-dataset']")
            main = header.find("div[@class='col-md-8 gn-record']")
            aside = header.find("aside[@class='col-md-4 gn-md-side']")
            self.assertIsNotNone(main.find("section[@class='izrk-eml-abstract']"))
            self.assertEqual(["overview", "keywords"],
                             [child.get("id") for child in aside])

    def test_abstract_follows_title_and_keywords_follow_image(self):
        root = ET.parse(PORTAL).getroot()
        template = next(node for node in root.findall(f"{XSL}template")
                        if node.get("name") == "eml-portal-record")
        header = next(node for node in template.iter("div")
                      if node.get("class") == "row izrk-record-header gn-card gn-card-dataset")
        main = next(node for node in header.findall("div")
                    if node.get("class") == "col-md-8 gn-record")
        aside = next(node for node in header.findall("aside")
                     if node.get("class") == "col-md-4 gn-md-side")
        abstract = next(node for node in main.findall(f"{XSL}if")
                        if node.get("test") == "normalize-space($metadata/dataset/abstract) != ''")
        section = abstract.find("section[@class='izrk-eml-abstract']")
        self.assertIsNotNone(section)
        self.assertEqual("Abstract", section.findtext("h2"))
        renderer = section.find(f"{XSL}call-template")
        self.assertEqual("render-paragraph-html", renderer.get("name"))
        self.assertEqual("$metadata/dataset/abstract",
                         renderer.find(f"{XSL}with-param").get("select"))
        self.assertIsNone(main.find(f"{XSL}call-template[@name='eml-keywords']"))
        self.assertEqual(["getOverviews", "eml-keywords"],
                         [node.get("mode") or node.get("name") for node in aside])

    def test_portal_keyword_list_links_to_existing_search_filter(self):
        view = ET.parse(VIEW).getroot()
        keywords = next(node for node in view.findall(f"{XSL}template")
                        if node.get("name") == "eml-keywords")
        link = keywords.find(".//a[@class='izrk-keyword-filter']")
        self.assertIsNotNone(link)
        self.assertIn('"tag.\\\\*"', link.get("href"))
        self.assertIn("{normalize-space(.)}", link.get("href"))


if __name__ == "__main__":
    unittest.main()
