"""Verify EML browse images become search result overviews."""

import json
import subprocess
import tempfile
import unittest
from zipfile import ZipFile
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[5]
STYLESHEET = (Path(__file__).resolve().parents[2]
              / "main/plugin/eml-gbif/index-fields/index.xsl")
WEBAPP = ROOT / "web/target/geonetwork/WEB-INF"
SAMPLE_MEF = (ROOT / "schemas/eml-gbif/src/main/plugin/eml-gbif/sample-data"
              / "eml-gbif-sample.mef")


@unittest.skipUnless((WEBAPP / "lib/saxon-9.1.0.8b-patch.jar").exists()
                     and (ROOT / "core/target/classes/org/fao/geonet/util/XslUtil.class").exists(),
                     "GeoNetwork build dependencies are required")
class OverviewIndexTest(unittest.TestCase):
    def transform(self, metadata, record_uuid=""):
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
                 f"-s:{source}", f"-xsl:{wrapper}", f"-o:{result}",
                 f"recordUuid={record_uuid}"],
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
        </eml:eml>''', record_uuid="record-1")
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
        </eml:eml>''', record_uuid="record-1")
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

    def test_geographic_extent_including_zero_coordinates_is_indexed(self):
        index = self.transform('''<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">
          <dataset><title>Equatorial extent</title><coverage><geographicCoverage>
            <boundingCoordinates>
              <westBoundingCoordinate>0</westBoundingCoordinate>
              <eastBoundingCoordinate>1</eastBoundingCoordinate>
              <southBoundingCoordinate>0</southBoundingCoordinate>
              <northBoundingCoordinate>1</northBoundingCoordinate>
            </boundingCoordinates>
          </geographicCoverage></coverage></dataset>
        </eml:eml>''')
        self.assertEqual("0.00", index.find("Field[@name='westBL']").get("string"))
        self.assertEqual("0.00", index.find("Field[@name='southBL']").get("string"))
        self.assertEqual("1.00", index.find("Field[@name='eastBL']").get("string"))
        self.assertEqual("1.00", index.find("Field[@name='northBL']").get("string"))
        self.assertEqual("0.00|0.00|1.00|1.00", index.find("Field[@name='geoBox']").get("string"))

    def test_legacy_eml_2_1_sample_indexes_its_map_extents(self):
        with ZipFile(SAMPLE_MEF) as archive:
            metadata = archive.read("metadata.xml").decode("utf-8")
        index = self.transform(metadata)
        self.assertEqual(2, len(index.findall("Field[@name='geoBox']")))
        self.assertGreater(int(index.findtext("tagNumber", "0")), 0)
        self.assertIsNotNone(index.find("resourceTitleObject"))

    def test_catalogue_uuid_is_used_without_alternate_identifier(self):
        index = self.transform('''<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
            packageId="00000000-0000-0000-0000-000000000001">
          <dataset><title>Example</title></dataset>
          <additionalMetadata><metadata><gbif>
            <resourceLogoUrl>cover.png</resourceLogoUrl>
          </gbif></metadata></additionalMetadata>
        </eml:eml>''', record_uuid="00000000-0000-0000-0000-000000000002")
        self.assertEqual("true", index.find("Field[@name='hasOverview']").get("string"))
        self.assertEqual(
            "https://catalogue.example/geonetwork/api/records/00000000-0000-0000-0000-000000000002/attachments/cover.png",
            json.loads(index.findtext("overview"))["url"])

    def test_valid_package_id_is_used_when_catalogue_uuid_is_unavailable(self):
        index = self.transform('''<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
            packageId="00000000-0000-0000-0000-000000000003">
          <dataset><title>Example</title></dataset>
          <additionalMetadata><metadata><gbif>
            <resourceLogoUrl>cover.png</resourceLogoUrl>
          </gbif></metadata></additionalMetadata>
        </eml:eml>''')
        self.assertEqual(
            "https://catalogue.example/geonetwork/api/records/00000000-0000-0000-0000-000000000003/attachments/cover.png",
            json.loads(index.findtext("overview"))["url"])

    def test_unchecked_package_id_cannot_form_local_attachment_url(self):
        index = self.transform('''<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
            packageId="not-a-record-uuid">
          <dataset><title>Example</title></dataset>
          <additionalMetadata><metadata><gbif>
            <resourceLogoUrl>cover.png</resourceLogoUrl>
          </gbif></metadata></additionalMetadata>
        </eml:eml>''')
        self.assertEqual("false", index.find("Field[@name='hasOverview']").get("string"))
        self.assertEqual([], index.findall("overview"))


if __name__ == "__main__":
    unittest.main()
