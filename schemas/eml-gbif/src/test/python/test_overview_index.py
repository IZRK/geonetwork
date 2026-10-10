"""Verify EML browse images become search result overviews."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[5]
STYLESHEET = (Path(__file__).resolve().parents[2]
              / "main/plugin/eml-gbif/index-fields/index.xsl")
WEBAPP = ROOT / "web/target/geonetwork/WEB-INF"


@unittest.skipUnless((WEBAPP / "lib/saxon-9.1.0.8b-patch.jar").exists()
                     and (ROOT / "core/target/classes/org/fao/geonet/util/XslUtil.class").exists(),
                     "GeoNetwork build dependencies are required")
class OverviewIndexTest(unittest.TestCase):
    def transform(self, metadata):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "metadata.xml"
            wrapper = directory / "index-test.xsl"
            result = directory / "index.xml"
            source.write_text(metadata, encoding="utf-8")
            wrapper.write_text(f'''<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:util="java:org.fao.geonet.util.XslUtil">
              <xsl:import href="{STYLESHEET.as_uri()}"/>
              <xsl:function name="util:getSettingValue">
                <xsl:param name="key"/>
                <xsl:sequence select="'https://catalogue.example/geonetwork/'"/>
              </xsl:function>
            </xsl:stylesheet>''', encoding="utf-8")
            classpath = f"{ROOT / 'core/target/classes'}:{WEBAPP / 'lib'}/*"
            process = subprocess.run(
                ["java", "-cp", classpath, "net.sf.saxon.Transform",
                 f"-s:{source}", f"-xsl:{wrapper}", f"-o:{result}"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            return ElementTree.parse(result).getroot()

    def test_local_logo_and_additional_image_are_indexed(self):
        index = self.transform('''<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">
          <dataset><alternateIdentifier>record-1</alternateIdentifier><title>Example</title>
            <additionalInfo><para>ISO additional browse image: second%20image.JPG</para></additionalInfo>
          </dataset><additionalMetadata><metadata><gbif>
            <resourceLogoUrl>first.png</resourceLogoUrl>
          </gbif></metadata></additionalMetadata>
        </eml:eml>''')
        self.assertEqual("true", index.find("Field[@name='hasOverview']").get("string"))
        self.assertEqual([
            "https://catalogue.example/geonetwork/api/records/record-1/attachments/first.png",
            "https://catalogue.example/geonetwork/api/records/record-1/attachments/second%20image.JPG",
        ], [json.loads(node.text)["url"] for node in index.findall("overview")])

    def test_unsafe_image_reference_is_not_indexed(self):
        index = self.transform('''<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">
          <dataset><alternateIdentifier>record-1</alternateIdentifier><title>Example</title></dataset>
          <additionalMetadata><metadata><gbif>
            <resourceLogoUrl>javascript:alert(1)</resourceLogoUrl>
          </gbif></metadata></additionalMetadata>
        </eml:eml>''')
        self.assertEqual("false", index.find("Field[@name='hasOverview']").get("string"))
        self.assertEqual([], index.findall("overview"))

    def test_external_image_url_is_kept(self):
        index = self.transform('''<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">
          <dataset><title>Example</title></dataset>
          <additionalMetadata><metadata><gbif>
            <resourceLogoUrl>https://images.example.org/cover.png</resourceLogoUrl>
          </gbif></metadata></additionalMetadata>
        </eml:eml>''')
        self.assertEqual("true", index.find("Field[@name='hasOverview']").get("string"))
        self.assertEqual("https://images.example.org/cover.png",
                         json.loads(index.findtext("overview"))["url"])


if __name__ == "__main__":
    unittest.main()
