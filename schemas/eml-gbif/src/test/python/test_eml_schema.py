"""Validate free-text keywords supported by migrated EML-GBIF records."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCHEMA = (Path(__file__).resolve().parents[2]
          / "main/plugin/eml-gbif/schema/eml-gbif-profile.xsd")


@unittest.skipUnless(shutil.which("xmllint"), "xmllint is required for XSD validation")
class EmlSchemaTest(unittest.TestCase):
    def test_keywords_without_invented_thesaurus_validate(self):
        document = '''<?xml version="1.0" encoding="UTF-8"?>
<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
  packageId="example" scope="system" system="https://example.org">
  <dataset>
    <title>Example dataset</title>
    <creator><organizationName>Example organization</organizationName></creator>
    <pubDate>2022-10-15</pubDate>
    <abstract><para>Example description.</para></abstract>
    <keywordSet><keyword>Copepoda</keyword><keyword>Cave biodiversity</keyword></keywordSet>
    <contact><organizationName>Example organization</organizationName></contact>
  </dataset>
  <additionalMetadata><metadata><gbif>
    <dateStamp>2026-02-12T11:02:41.655Z</dateStamp>
    <resourceLogoUrl>copepoda.jpg</resourceLogoUrl>
  </gbif></metadata></additionalMetadata>
</eml:eml>'''
        with tempfile.TemporaryDirectory() as temporary:
            metadata = Path(temporary) / "metadata.xml"
            metadata.write_text(document, encoding="utf-8")
            result = subprocess.run(
                ["xmllint", "--nonet", "--noout", "--schema", str(SCHEMA), str(metadata)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
