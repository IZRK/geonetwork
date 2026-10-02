"""Regression coverage for the EML-Gbif formatter's shared XSL helpers."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


STYLESHEET = (Path(__file__).resolve().parents[2]
              / "main/plugin/eml-gbif/formatter/citation/base.xsl")
EML_NS = "https://eml.ecoinformatics.org/eml-2.2.0"


class FormatterCitationTest(unittest.TestCase):
    def transform(self, source):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "input.xml").write_text(source)
            wrapper = directory / "wrapper.xsl"
            wrapper.write_text(f'''<xsl:stylesheet
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:eml="{EML_NS}"
                xmlns:eml-fn="http://geonetwork-opensource.org/xsl/functions/eml"
                version="2.0">
              <xsl:include href="{STYLESHEET.as_uri()}"/>
              <xsl:output method="xml"/>
              <xsl:template match="/">
                <result>
                  <first-key><xsl:value-of select="eml-fn:party-key(//creator[1])"/></first-key>
                  <same-key><xsl:value-of select="eml-fn:party-key(//associatedParty[1])"/></same-key>
                  <name><xsl:value-of select="eml-fn:party-name(//creator[1])"/></name>
                  <roles><xsl:value-of select="eml-fn:party-roles(//creator[1], /root)"/></roles>
                  <field-key><xsl:value-of select="eml-fn:field-key(//creator[1]/role[1])"/></field-key>
                  <xsl:call-template name="get-eml-citation">
                    <xsl:with-param name="metadata" select="/root/eml:eml"/>
                    <xsl:with-param name="uuid" select="'record-1'"/>
                    <xsl:with-param name="nodeUrl" select="'https://catalogue.example/'"/>
                  </xsl:call-template>
                </result>
              </xsl:template>
            </xsl:stylesheet>''')
            result = directory / "result.xml"
            subprocess.run([
                "java", "-cp", os.environ["SAXON_JAR"], "net.sf.saxon.Transform",
                f"-s:{directory / 'input.xml'}", f"-xsl:{wrapper}", f"-o:{result}",
            ], check=True, capture_output=True, text=True)
            return ET.parse(result).getroot()

    def test_party_helpers_and_citation_template_compile_and_render(self):
        result = self.transform(f'''<root xmlns:eml="{EML_NS}">
          <eml:eml><dataset>
            <title>Example dataset</title><pubDate>2022-10-15</pubDate>
            <creator><individualName><givenName>Jane</givenName>
              <surName>Doe</surName></individualName>
              <organizationName>Institute</organizationName>
              <role>author</role><role>curator</role>
            </creator>
            <associatedParty><individualName><givenName>Jane</givenName>
              <surName>Doe</surName></individualName>
              <organizationName>Institute</organizationName>
            </associatedParty>
          </dataset></eml:eml>
        </root>''')

        self.assertEqual(result.findtext("first-key"), result.findtext("same-key"))
        self.assertEqual("Jane Doe", result.findtext("name"))
        self.assertEqual("author · curator", result.findtext("roles"))
        self.assertIn("role", result.findtext("field-key"))
        self.assertEqual("Example dataset", result.findtext("citation/translatedTitle"))
        self.assertEqual("Jane Doe", result.findtext("citation/authorsNameAndOrgList/author"))
        self.assertEqual("2022-10-15", result.findtext("citation/lastPublicationDate"))
        self.assertEqual("https://catalogue.example/api/records/record-1",
                         result.findtext("citation/landingPageUrl"))


if __name__ == "__main__":
    unittest.main()
