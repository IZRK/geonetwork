"""Run the EML index stylesheet without a live GeoNetwork application context."""

import os
from pathlib import Path
import subprocess
import tempfile
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
STYLESHEET = ROOT / "schemas/eml-gbif/src/main/plugin/eml-gbif/index-fields/index.xsl"
WEBAPP = ROOT / "web/target/geonetwork/WEB-INF"


def index_dependencies_available() -> bool:
    return ((WEBAPP / "lib/saxon-9.1.0.8b-patch.jar").exists()
            and (ROOT / "core/target/classes/org/fao/geonet/util/XslUtil.class").exists())


def render_index(metadata: bytes, record_uuid: str) -> ET.Element:
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        source = directory / "metadata.xml"
        wrapper = directory / "index-test.xsl"
        result = directory / "index.xml"
        source.write_bytes(metadata)
        wrapper.write_text(f'''<xsl:stylesheet version="2.0"
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
            xmlns:util="java:org.fao.geonet.util.XslUtil">
          <xsl:import href="{STYLESHEET.as_uri()}"/>
          <xsl:function name="util:getSettingValue">
            <xsl:param name="key"/>
            <xsl:sequence select="'https://catalogue.example/geonetwork/'"/>
          </xsl:function>
        </xsl:stylesheet>''', encoding="utf-8")
        classpath = os.pathsep.join((str(ROOT / "core/target/classes"),
                                     str(WEBAPP / "lib" / "*")))
        process = subprocess.run(
            ["java", "-cp", classpath,
             "net.sf.saxon.Transform", f"-s:{source}", f"-xsl:{wrapper}",
             f"-o:{result}", f"recordUuid={record_uuid}"],
            capture_output=True, text=True, check=False)
        if process.returncode:
            raise AssertionError(process.stderr)
        return ET.parse(result).getroot()
