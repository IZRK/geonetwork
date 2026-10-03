"""Render a named metadata provider in the existing Contacts section."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


VIEW = (Path(__file__).resolve().parents[2]
        / "main/plugin/eml-gbif/formatter/xsl-view/view.xsl")
CITATION = VIEW.parents[1] / "citation/base.xsl"


class MetadataContactTest(unittest.TestCase):
    def test_named_metadata_provider_has_own_contact_card(self):
        source = '''<root xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">
          <eml:eml><dataset><metadataProvider>
            <individualName><givenName>Magdalena</givenName><surName>Aljančič</surName></individualName>
            <electronicMailAddress>magdalena.aljancic@zrc-sazu.si</electronicMailAddress>
          </metadataProvider><contact>
            <individualName><givenName>Tanja</givenName><surName>Pipan</surName></individualName>
            <organizationName>IZRK ZRC SAZU</organizationName>
            <electronicMailAddress>tanja.pipan@zrc-sazu.si</electronicMailAddress>
          </contact></dataset></eml:eml>
        </root>'''
        party_template = re.search(
            r'<xsl:template name="eml-party-table">.*?</xsl:template>',
            VIEW.read_text(encoding="utf-8"), re.DOTALL).group()
        email_template = re.search(
            r'<xsl:template mode="render-field" match="electronicMailAddress\|userId".*?</xsl:template>',
            VIEW.read_text(encoding="utf-8"), re.DOTALL).group()
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            metadata = directory / "metadata.xml"
            stylesheet = directory / "contacts.xsl"
            output = directory / "contacts.xml"
            metadata.write_text(source, encoding="utf-8")
            stylesheet.write_text(f'''<xsl:stylesheet version="2.0"
              xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
              xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
              xmlns:eml-fn="http://geonetwork-opensource.org/xsl/functions/eml">
              <xsl:include href="{CITATION.as_uri()}"/>
              <xsl:variable name="metadata" select="/root/eml:eml"/>
              <xsl:variable name="schemaStrings" select="/root/strings"/>
              {party_template}
              {email_template}
              <xsl:template match="/"><result><xsl:call-template name="eml-party-table">
                <xsl:with-param name="label" select="'Contacts'"/>
                <xsl:with-param name="nodes" select="$metadata/dataset/*[self::metadataProvider or self::contact]"/>
              </xsl:call-template></result></xsl:template>
              <xsl:template name="node-label"><xsl:text>Email</xsl:text></xsl:template>
              <xsl:template match="node()|@*" mode="render-field"/>
            </xsl:stylesheet>''', encoding="utf-8")
            result = subprocess.run(
                ["java", "-cp", os.environ["SAXON_JAR"], "net.sf.saxon.Transform",
                 f"-s:{metadata}", f"-xsl:{stylesheet}", f"-o:{output}"],
                capture_output=True, text=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            section = ET.parse(output).getroot().find("section")
            self.assertEqual("Contacts", section.findtext("h2"))
            cards = section.findall("div/details")
            self.assertEqual(2, len(cards))
            self.assertEqual({"IZRK ZRC SAZU", "Contacts"},
                             {card.findtext("summary/span") for card in cards})
            email_card = next(card for card in cards
                              if card.findtext("summary/span") == "Contacts")
            link = email_card.find(".//a")
            self.assertEqual("Magdalena Aljančič", email_card.findtext(".//h4"))
            self.assertEqual("mailto:magdalena.aljancic@zrc-sazu.si", link.get("href"))
            self.assertEqual("magdalena.aljancic@zrc-sazu.si", link.text)


if __name__ == "__main__":
    unittest.main()
