"""Check that EML keywords populate the fields used by search filters."""

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


@unittest.skipUnless((WEBAPP / "lib/saxon-9.1.0.8b-patch.jar").exists(),
                     "GeoNetwork webapp dependencies are required")
class KeywordIndexTest(unittest.TestCase):
    def test_free_text_keywords_are_indexed_for_tag_filters(self):
        metadata = '''<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">
          <dataset><title>Example</title><keywordSet>
            <keyword>Copepoda</keyword><keyword>Cave biodiversity</keyword>
          </keywordSet></dataset>
        </eml:eml>'''
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "metadata.xml"
            result = Path(temporary) / "index.xml"
            source.write_text(metadata, encoding="utf-8")
            classpath = f"{WEBAPP / 'classes'}:{WEBAPP / 'lib'}/*"
            process = subprocess.run(
                ["java", "-cp", classpath, "net.sf.saxon.Transform",
                 f"-s:{source}", f"-xsl:{STYLESHEET}", f"-o:{result}"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, process.returncode, process.stderr)

            index = ElementTree.parse(result).getroot()
            tags = json.loads(index.findtext("tag"))
            badges = json.loads(index.findtext("allKeywords"))
            expected = ["Copepoda", "Cave biodiversity"]
            self.assertEqual(expected, [item["default"] for item in tags])
            self.assertEqual("2", index.findtext("tagNumber"))
            self.assertEqual(expected, [item["default"] for item in
                                        badges["otherKeywords-theme"]["keywords"]])


if __name__ == "__main__":
    unittest.main()
