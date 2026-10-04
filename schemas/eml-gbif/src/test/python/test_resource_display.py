"""Check EML distribution cards and preserved browse images."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


VIEW = (Path(__file__).resolve().parents[2]
        / "main/plugin/eml-gbif/formatter/xsl-view/view.xsl")


class ResourceDisplayTest(unittest.TestCase):
    def test_download_links_and_two_overviews(self):
        view = VIEW.read_text(encoding="utf-8")
        resolver = re.search(
            r'<xsl:function name="eml-fn:resolve-resource-logo-url".*?</xsl:function>',
            view, re.DOTALL).group()
        overview = re.search(
            r'<xsl:template mode="getOverviews" match="eml:eml">.*?</xsl:template>',
            view, re.DOTALL).group()
        distribution = re.search(
            r'<xsl:template name="eml-distribution">.*?</xsl:template>',
            view, re.DOTALL).group()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "record.xml"
            stylesheet = directory / "view-test.xsl"
            output = directory / "rendered.xml"
            source.write_text('''<root xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">
              <strings><overviews>Overview</overviews><overview>Image</overview></strings>
              <eml:eml><dataset><additionalInfo><para>ISO citation date (creation): 2024-02-10
ISO additional browse image: second.png</para></additionalInfo>
                <distribution><online><onlineDescription>Trait%20data.xlsx</onlineDescription>
                  <url>https://example.org/attachments/trait%20data.xlsx</url>
                </online></distribution>
                <distribution><online><onlineDescription>Figshare collection</onlineDescription>
                  <url>https://figshare.example/collections/1</url>
                </online></distribution>
                <distribution><online><url>javascript:alert(1)</url></online></distribution>
              </dataset><additionalMetadata><metadata><gbif>
                <resourceLogoUrl>first.png</resourceLogoUrl>
              </gbif></metadata></additionalMetadata></eml:eml>
            </root>''', encoding="utf-8")
            stylesheet.write_text(f'''<xsl:stylesheet version="2.0"
              xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
              xmlns:xs="http://www.w3.org/2001/XMLSchema"
              xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
              xmlns:eml-fn="http://geonetwork-opensource.org/xsl/functions/eml"
              exclude-result-prefixes="#all">
              <xsl:variable name="metadata" select="/root/eml:eml"/>
              <xsl:variable name="metadataUuid" select="'record-1'"/>
              <xsl:variable name="nodeUrl" select="'https://catalogue.example/'"/>
              <xsl:variable name="schemaStrings" select="/root/strings"/>
              {resolver}
              {overview}
              {distribution}
              <xsl:template match="/"><result>
                <xsl:apply-templates select="/root/eml:eml" mode="getOverviews"/>
                <xsl:call-template name="eml-distribution"/>
              </result></xsl:template>
            </xsl:stylesheet>''', encoding="utf-8")
            process = subprocess.run(
                ["java", "-cp", os.environ["SAXON_JAR"], "net.sf.saxon.Transform",
                 f"-s:{source}", f"-xsl:{stylesheet}", f"-o:{output}"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            rendered = ET.parse(output).getroot()
            self.assertEqual(
                ["https://catalogue.example/api/records/record-1/attachments/first.png",
                 "https://catalogue.example/api/records/record-1/attachments/second.png"],
                [image.get("src") for image in rendered.findall(".//section/img") +
                 rendered.findall(".//section/div/img")],
            )
            distribution_section = rendered.find("div[@id='gn-section-eml-distribution']")
            self.assertEqual(["Download", "Links"],
                             [heading.text for heading in distribution_section.findall("h2")])
            cards = distribution_section.findall(".//div[@class='izrk-eml-resource-card']")
            self.assertEqual(2, len(cards))
            self.assertEqual("Trait data.xlsx", cards[0].findtext("div[@class='izrk-eml-resource-label']/a"))
            self.assertEqual("XLSX", cards[0].findtext("div[@class='izrk-eml-resource-icon']/span"))
            self.assertEqual("Figshare collection", cards[1].findtext("div[@class='izrk-eml-resource-label']/a"))
            self.assertEqual(["Download", "Open link"],
                             [card.findtext("a[@class='btn btn-default izrk-eml-resource-action']")
                              for card in cards])
            self.assertEqual("https://example.org/attachments/trait%20data.xlsx",
                             cards[0].find("a[@class='btn btn-default izrk-eml-resource-action']").get("href"))


if __name__ == "__main__":
    unittest.main()
