"""Regression tests for the source-backed Copepoda taxonomy package."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from _migrations.build_copepoda_taxonomy import DEFAULT_MEF, METADATA, build, embed_taxonomy


SCHEMA = (Path(__file__).resolve().parents[1]
          / "schemas/eml-gbif/src/main/plugin/eml-gbif/schema/eml.xsd")
ROOT = Path(__file__).resolve().parents[1]
RIF = ROOT / "schemas/eml-gbif/src/main/plugin/eml-gbif/convert/rif.xsl"


class CopepodaTaxonomyTest(unittest.TestCase):
    def test_mef_has_complete_nested_taxonomy_and_validates(self):
        with ZipFile(DEFAULT_MEF) as archive:
            metadata = archive.read(METADATA)
            root = ET.fromstring(metadata)
            coverage = root.find("./dataset/coverage/taxonomicCoverage")
            orders = coverage.findall("taxonomicClassification")
            self.assertEqual({"Cyclopoida": 2, "Harpacticoida": 28}, {
                node.findtext("taxonRankValue"): len(node.findall("taxonomicClassification"))
                for node in orders})
            self.assertEqual(32, len(coverage.findall(".//taxonomicClassification")))
            self.assertEqual(6, len(archive.namelist()))

        with tempfile.TemporaryDirectory() as directory:
            xml = Path(directory) / "metadata.xml"
            xml.write_bytes(metadata)
            subprocess.run(["xmllint", "--noout", "--schema", str(SCHEMA), str(xml)],
                           check=True, capture_output=True, text=True)

    def test_rebuild_preserves_other_mef_members(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "rebuilt.mef"
            build(DEFAULT_MEF, output)
            with ZipFile(DEFAULT_MEF) as source, ZipFile(output) as rebuilt:
                self.assertEqual(source.namelist(), rebuilt.namelist())
                for name in source.namelist():
                    if name == METADATA:
                        self.assertEqual(ET.tostring(ET.fromstring(source.read(name))),
                                         ET.tostring(ET.fromstring(rebuilt.read(name))))
                    else:
                        self.assertEqual(source.read(name), rebuilt.read(name))

    def test_rejects_incomplete_taxonomy(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "taxonomy.csv"
            bad.write_text("species,order\nDiacyclops languidoides,Cyclopoida\n")
            with ZipFile(DEFAULT_MEF) as archive:
                with self.assertRaisesRegex(ValueError, "do not match"):
                    embed_taxonomy(archive.read(METADATA), bad)

    @unittest.skipUnless(os.environ.get("SAXON_JAR") and
                         (ROOT / "core/target/classes/org/fao/geonet/util/Sha1Encoder.class").exists(),
                         "Saxon and compiled GeoNetwork classes are required")
    def test_rif_export_keeps_nested_taxon_names_separate(self):
        with ZipFile(DEFAULT_MEF) as archive:
            metadata = ET.fromstring(archive.read(METADATA))
        names = {node.text for node in metadata.findall(
            "./dataset/coverage/taxonomicCoverage//taxonRankValue")}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.xml"
            output = Path(directory) / "rif.xml"
            root = ET.Element("root")
            env = ET.SubElement(root, "env")
            ET.SubElement(env, "siteName").text = "Test"
            ET.SubElement(env, "siteURL").text = "https://example.test"
            root.append(metadata)
            ET.ElementTree(root).write(source, encoding="utf-8", xml_declaration=True)
            classpath = os.pathsep.join([
                os.environ["SAXON_JAR"], str(ROOT / "core/target/classes"),
                str(ROOT / "common/target/classes")])
            subprocess.run(["java", "-cp", classpath, "net.sf.saxon.Transform",
                            f"-s:{source}", f"-xsl:{RIF}", f"-o:{output}"],
                           check=True, capture_output=True, text=True)
            subjects = {node.text for node in ET.parse(output).getroot().iter()
                        if node.tag.rsplit("}", 1)[-1] == "subject"}
        self.assertTrue(names <= subjects)


if __name__ == "__main__":
    unittest.main()
