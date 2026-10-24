"""Render EML keyword links and check their decoded search queries."""

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from urllib.parse import parse_qsl, urlsplit
from xml.etree import ElementTree as ET


VIEW = (Path(__file__).resolve().parents[2]
        / "main/plugin/eml-gbif/formatter/xsl-view/view.xsl")
XSL_URI = "http://www.w3.org/1999/XSL/Transform"
XSL = f"{{{XSL_URI}}}"
EML_URI = "https://eml.ecoinformatics.org/eml-2.2.0"
FUNCTION_URI = "http://geonetwork-opensource.org/xsl/functions/eml"


class KeywordLinkTest(unittest.TestCase):
    def test_side_and_portal_links_encode_the_full_query(self):
        keywords = ["Copepoda", "A&B", 'Quote " and backslash \\',
                    'x":false,"other', "hash #?= % /", "Življenje", "a{b}:true"]
        source = ET.Element("root")
        eml = ET.SubElement(source, f"{{{EML_URI}}}eml")
        dataset = ET.SubElement(eml, "dataset")
        keyword_set = ET.SubElement(dataset, "keywordSet")
        ET.SubElement(keyword_set, "keywordThesaurus").text = "Example"
        for keyword in keywords:
            ET.SubElement(keyword_set, "keyword").text = keyword

        stylesheet = ET.Element(f"{XSL}stylesheet", {
            "version": "2.0", "xmlns:eml": EML_URI,
            "xmlns:eml-fn": FUNCTION_URI,
            "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
        })
        view = ET.parse(VIEW).getroot()
        for node in view:
            if (node.tag == f"{XSL}function" and node.get("name") == "eml-fn:keyword-search-href"
                    or node.tag == f"{XSL}template" and
                    (node.get("name") == "eml-keywords" or node.get("mode") == "getTags")):
                stylesheet.append(copy.deepcopy(node))
        ET.SubElement(stylesheet, f"{XSL}variable", {
            "name": "metadata", "select": "/root/eml:eml"})
        strings = ET.SubElement(ET.SubElement(stylesheet, f"{XSL}variable", {
            "name": "schemaStrings"}), "schemaStrings")
        ET.SubElement(strings, "noThesaurusName").text = "Keywords"
        template = ET.SubElement(stylesheet, f"{XSL}template", {"match": "/"})
        result = ET.SubElement(template, "result")
        side = ET.SubElement(result, "side")
        ET.SubElement(side, f"{XSL}apply-templates", {
            "select": "/root/eml:eml", "mode": "getTags"})
        grouped = ET.SubElement(result, "grouped")
        grouped_tags = ET.SubElement(grouped, f"{XSL}apply-templates", {
            "select": "/root/eml:eml", "mode": "getTags"})
        ET.SubElement(grouped_tags, f"{XSL}with-param", {
            "name": "byThesaurus", "select": "true()"})
        portal = ET.SubElement(result, "portal")
        ET.SubElement(portal, f"{XSL}call-template", {"name": "eml-keywords"})

        ET.register_namespace("xsl", XSL_URI)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            input_path = directory / "record.xml"
            stylesheet_path = directory / "keywords.xsl"
            output_path = directory / "result.xml"
            ET.ElementTree(source).write(input_path, encoding="utf-8", xml_declaration=True)
            ET.ElementTree(stylesheet).write(stylesheet_path, encoding="utf-8", xml_declaration=True)
            process = subprocess.run(
                ["java", "-cp", os.environ["SAXON_JAR"], "net.sf.saxon.Transform",
                 f"-s:{input_path}", f"-xsl:{stylesheet_path}", f"-o:{output_path}"],
                capture_output=True, text=True, check=False)
            self.assertEqual(0, process.returncode, process.stderr)
            rendered = ET.parse(output_path).getroot()

        for section in ("side", "grouped", "portal"):
            with self.subTest(section=section):
                links = rendered.findall(f"{section}//a")
                self.assertCountEqual(keywords, [link.text for link in links])
                for link in links:
                    keyword = link.text
                    href = link.get("href")
                    self.assertTrue(href.startswith("#/search?query_string="))
                    self.assertNotIn("&", href)
                    self.assertNotIn('"', href)
                    parameters = parse_qsl(urlsplit(href).fragment.split("?", 1)[1])
                    self.assertEqual(1, len(parameters))
                    self.assertEqual("query_string", parameters[0][0])
                    self.assertEqual({r"tag.\*": {keyword: True}},
                                     json.loads(parameters[0][1]))


if __name__ == "__main__":
    unittest.main()
