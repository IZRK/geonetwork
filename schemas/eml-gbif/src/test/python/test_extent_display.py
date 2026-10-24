"""Ensure metadata extent coordinates render as fixed text, not form fields."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


RENDER_FUNCTIONS = (Path(__file__).resolve().parents[5]
                    / "web/src/main/webapp/WEB-INF/data/data/formatter/xslt/render-functions.xsl")
XSL = "{http://www.w3.org/1999/XSL/Transform}"


class ExtentDisplayTest(unittest.TestCase):
    def test_bbox_coordinates_are_static_text(self):
        functions = ET.parse(RENDER_FUNCTIONS).getroot()
        bbox = next(node for node in functions.findall(f"{XSL}function")
                    if node.get("name") == "gn-fn-render:bbox")
        geometry = next(node for node in functions.findall(f"{XSL}function")
                         if node.get("name") == "gn-fn-render:geometry")

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "record.xml"
            stylesheet = directory / "extent-test.xsl"
            output = directory / "rendered.xml"
            source.write_text("""<root><strings><north>North</north><south>South</south>
              <east>East</east><west>West</west><thumbnail>Extent map</thumbnail></strings></root>""",
                              encoding="utf-8")
            stylesheet.write_text(f"""<xsl:stylesheet version="2.0"
              xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
              xmlns:xs="http://www.w3.org/2001/XMLSchema"
              xmlns:gn-fn-render="http://geonetwork-opensource.org/xsl/functions/render">
              <xsl:variable name="schemaStrings" select="/root/strings"/>
              <xsl:variable name="nodeUrl" select="'https://catalogue.example/'"/>
              {ET.tostring(bbox, encoding="unicode")}
              {ET.tostring(geometry, encoding="unicode")}
              <xsl:template match="/root">
                <xsl:sequence select="gn-fn-render:bbox(13.8, 45.6, 14.52, 45.84)"/>
              </xsl:template>
            </xsl:stylesheet>""", encoding="utf-8")

            process = subprocess.run(
                ["java", "-cp", os.environ["SAXON_JAR"], "net.sf.saxon.Transform",
                 f"-s:{source}", f"-xsl:{stylesheet}", f"-o:{output}"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, process.returncode, process.stderr)

            rendered = ET.parse(output).getroot()
            self.assertEqual([], rendered.findall(".//input"))
            values = rendered.findall(".//span[@class='form-control']")
            self.assertEqual(["45.84", "45.60", "14.52", "13.80"],
                             [value.text for value in values])
            self.assertEqual(["North", "South", "East", "West"],
                             [value.get("aria-label") for value in values])
            self.assertEqual("https://catalogue.example/api/regions/geom.png?geomsrs=EPSG:4326&geom=POLYGON((14.52%2045.6,14.52%2045.84,13.8%2045.84,13.8%2045.6,14.52%2045.6))",
                             rendered.find(".//img").get("src"))


if __name__ == "__main__":
    unittest.main()
