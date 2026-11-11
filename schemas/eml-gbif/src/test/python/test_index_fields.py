"""Run with GEONETWORK_LIB_DIR pointing to a built webapp's WEB-INF/lib.

Exercises the real indexing stylesheet and Elasticsearch JSON converter without
starting a catalogue or Elasticsearch server.
"""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree as ET


STYLESHEET = (Path(__file__).resolve().parents[2]
              / "main/plugin/eml-gbif/index-fields/index.xsl")
CONVERTER = (Path(__file__).resolve().parents[5]
             / "core/src/main/java/org/fao/geonet/kernel/search/EsSearchManager.java")
EML = "https://eml.ecoinformatics.org/eml-2.2.0"


@unittest.skipUnless(os.environ.get("GEONETWORK_LIB_DIR"),
                     "GEONETWORK_LIB_DIR is required")
class IndexFieldsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.work = Path(cls.directory.name)
        cls.classpath = str(Path(os.environ["GEONETWORK_LIB_DIR"]).resolve() / "*")
        source = cls.work / "IndexDocument.java"
        source.write_text('''import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import javax.xml.transform.stream.StreamSource;
import javax.xml.transform.stream.StreamResult;
import org.fao.geonet.kernel.search.EsSearchManager;
import org.jdom.input.SAXBuilder;
import java.io.ByteArrayInputStream;

public class IndexDocument {
    public static void main(String[] args) throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        new net.sf.saxon.TransformerFactoryImpl()
            .newTransformer(new StreamSource(args[0]))
            .transform(new StreamSource(args[1]), new StreamResult(output));
        org.jdom.Element fields = new SAXBuilder()
            .build(new ByteArrayInputStream(output.toByteArray())).getRootElement();
        Files.write(Paths.get(args[2]), new EsSearchManager()
            .documentToJson(fields).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
}
''', encoding="utf-8")
        subprocess.run(["javac", "--release", "11", "-cp", cls.classpath,
                        "-d", str(cls.work), str(CONVERTER), str(source)],
                       check=True, capture_output=True, text=True)

    def index(self, abstract, logo=None):
        root = ET.Element(f"{{{EML}}}eml", packageId="example", scope="system", system="test")
        dataset = ET.SubElement(root, "dataset")
        ET.SubElement(dataset, "title").text = "Example"
        dataset.append(ET.fromstring(abstract))
        if logo:
            gbif = ET.SubElement(ET.SubElement(ET.SubElement(root, "additionalMetadata"),
                                             "metadata"), "gbif")
            ET.SubElement(gbif, "resourceLogoUrl").text = logo
        input_path = self.work / "input.xml"
        output_path = self.work / "index.json"
        ET.ElementTree(root).write(input_path, encoding="utf-8")
        subprocess.run(["java", "-cp", os.pathsep.join([str(self.work), self.classpath]),
                        "IndexDocument", str(STYLESHEET), str(input_path), str(output_path)],
                       check=True, capture_output=True, text=True)
        return json.loads(output_path.read_text(encoding="utf-8"))

    def test_mixed_abstract_keeps_sections_inline_text_and_paragraph_breaks(self):
        result = self.index('''<abstract>Opening text.
          <para>First <emphasis>paragraph</emphasis>.</para>
          <section><title>Methods</title><para>Section content.</para>
            <section><title>Details</title><para>Nested content.</para></section>
          </section><para>Last paragraph.</para>Closing text.</abstract>''')
        expected = ("Opening text.\n\nFirst paragraph.\n\nMethods\n\nSection content."
                    "\n\nDetails\n\nNested content.\n\nLast paragraph.\n\nClosing text.")
        self.assertEqual(expected, result["resourceAbstract"])
        self.assertEqual({"default": expected, "langeng": expected},
                         result["resourceAbstractObject"])

    def test_plain_text_abstract_is_preserved(self):
        self.assertEqual("Plain text abstract.", self.index(
            "<abstract> Plain text   abstract. </abstract>")["resourceAbstract"])

    def test_overview_sets_a_searchable_flag(self):
        result = self.index("<abstract><para>Example.</para></abstract>",
                            "https://example.org/image.png")
        self.assertEqual("true", result["hasOverview"])
        self.assertEqual("https://example.org/image.png", result["overview"][0]["url"])

    def test_missing_overview_sets_false(self):
        result = self.index("<abstract><para>Example.</para></abstract>")
        self.assertEqual("false", result["hasOverview"])
        self.assertNotIn("overview", result)


if __name__ == "__main__":
    unittest.main()
