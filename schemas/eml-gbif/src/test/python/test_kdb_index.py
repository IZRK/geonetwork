"""Exercise the pure KDB EML index module with Saxon and the migration MEFs."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from zipfile import ZipFile
from xml.etree import ElementTree as ET


SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "main/plugin/eml-gbif"
MODULE = SCHEMA_ROOT / "index-fields/kdb-fields.xsl"
MIGRATIONS = SCHEMA_ROOT.parents[5].parent / "geonetwork-eml-migrations"


def local_name(element):
    return element.tag.rsplit("}", 1)[-1]


def mef_eml(path):
    with ZipFile(path) as package:
        for name in package.namelist():
            if not name.lower().endswith(".xml"):
                continue
            try:
                root = ET.fromstring(package.read(name))
            except ET.ParseError:
                continue
            if local_name(root) == "eml":
                return root
    raise AssertionError(f"No EML root found in {path.name}")


@unittest.skipUnless(os.environ.get("SAXON_JAR"), "SAXON_JAR is required")
class KdbIndexModuleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.work = Path(cls.directory.name)
        cls.wrapper = cls.work / "wrapper.xsl"
        cls.input = cls.work / "input.xml"
        cls.output = cls.work / "output.xml"
        cls.wrapper.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:kdb="http://geonetwork-opensource.org/xsl/functions/kdb-eml"
  exclude-result-prefixes="kdb">
  <xsl:include href="{MODULE.as_uri()}"/>
  <xsl:output method="xml" encoding="UTF-8"/>
  <xsl:template match="/">
    <results>
      <xsl:for-each select="cases/case">
        <result name="{{@name}}">
          <xsl:variable name="eml" select="*[1]"/>
          <xsl:call-template name="kdb:index-fields">
            <xsl:with-param name="eml" select="$eml"/>
            <xsl:with-param name="dataset" select="$eml/*[local-name() = 'dataset'][1]"/>
          </xsl:call-template>
        </result>
      </xsl:for-each>
      <escaped><xsl:value-of select="kdb:json-string(concat('quote', codepoints-to-string(34), codepoints-to-string(92), 'slash', codepoints-to-string(9)))"/></escaped>
    </results>
  </xsl:template>
</xsl:stylesheet>
''', encoding="utf-8")

        root = ET.Element("cases")
        synthetic = ET.SubElement(root, "case", name="synthetic")
        eml = ET.SubElement(synthetic, "eml")
        dataset = ET.SubElement(eml, "dataset")
        for _ in range(2):
            creator = ET.SubElement(dataset, "creator")
            individual = ET.SubElement(creator, "individualName")
            ET.SubElement(individual, "givenName").text = "Ana"
            ET.SubElement(individual, "surName").text = "Novak"
            ET.SubElement(creator, "organizationName").text = "IZRK"
            ET.SubElement(creator, "electronicMailAddress").text = 'ana"\\example.test'
        contact = ET.SubElement(dataset, "contact")
        ET.SubElement(contact, "organizationName").text = "Contact office"
        associated = ET.SubElement(dataset, "associatedParty")
        ET.SubElement(associated, "individualName")
        ET.SubElement(associated, "organizationName").text = "Associated org"
        ET.SubElement(associated, "role").text = "principalInvestigator"
        publisher = ET.SubElement(dataset, "publisher")
        ET.SubElement(publisher, "organizationName").text = "Publisher org"
        ET.SubElement(dataset, "alternateIdentifier").text = 'local "identifier"\\one'
        ET.SubElement(dataset, "alternateIdentifier").text = "   "
        distribution = ET.SubElement(dataset, "distribution")
        online = ET.SubElement(distribution, "online")
        ET.SubElement(online, "url", function="download").text = "https://example.test/data.csv"
        ET.SubElement(online, "onlineDescription").text = 'CSV "download"'
        rejected = ET.SubElement(distribution, "online")
        ET.SubElement(rejected, "url").text = "mailto:data@example.test"
        coverage = ET.SubElement(dataset, "coverage")
        geographic = ET.SubElement(coverage, "geographicCoverage")
        for coords in [("14.123456", "45.1", "14.9", "45.8"), ("13.8", "45.0", "15.0", "46.0"), ("20", "10", "19", "12"), ("NaN", "0", "1", "1")]:
            box = ET.SubElement(geographic, "boundingCoordinates")
            for name, value in zip(("westBoundingCoordinate", "southBoundingCoordinate", "eastBoundingCoordinate", "northBoundingCoordinate"), coords):
                ET.SubElement(box, name).text = value
        additional = ET.SubElement(eml, "additionalMetadata")
        metadata = ET.SubElement(additional, "metadata")
        gbif = ET.SubElement(metadata, "gbif")
        ET.SubElement(gbif, "hierarchyLevel").text = "researchSite"
        physical = ET.SubElement(gbif, "physical")
        data_format = ET.SubElement(physical, "dataFormat")
        defined = ET.SubElement(data_format, "externallyDefinedFormat")
        ET.SubElement(defined, "formatName").text = "CSV"
        table = ET.SubElement(dataset, "dataTable")
        table_physical = ET.SubElement(table, "physical")
        ET.SubElement(table_physical, "objectName").text = "observations.tsv"
        table_format = ET.SubElement(table_physical, "dataFormat")
        ET.SubElement(table_format, "textFormat")

        for package in sorted(MIGRATIONS.glob("*.mef")):
            case = ET.SubElement(root, "case", name=package.name)
            case.append(mef_eml(package))
        ET.ElementTree(root).write(cls.input, encoding="utf-8", xml_declaration=True)
        try:
            subprocess.run([
                "java", "-cp", os.environ["SAXON_JAR"], "net.sf.saxon.Transform",
                f"-s:{cls.input}", f"-xsl:{cls.wrapper}", f"-o:{cls.output}",
            ], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(error.stderr) from error
        cls.results = ET.parse(cls.output).getroot()
        cls.cases = {case.attrib["name"]: case for case in cls.results.findall("result")}

    @staticmethod
    def fields(case):
        return [
            {**field.attrib, "value": field.attrib.get("string", "")}
            for field in case.findall("Field")
        ]

    @classmethod
    def named(cls, case, name):
        return [field for field in cls.fields(case) if field["name"] == name]

    def test_json_escaping_handles_quotes_slashes_and_control_codepoints(self):
        self.assertEqual(r'quote\"\\slash\t', self.results.findtext("escaped"))

    def test_synthetic_contract_projects_parties_links_formats_and_boxes(self):
        fields = self.fields(self.cases["synthetic"])
        scalars = {field["name"]: field["value"] for field in fields if field.get("type") != "object"}
        self.assertEqual("eml-gbif", scalars["kdbMetadataSchema"])
        self.assertEqual("1", scalars["kdbIndexVersion"])
        self.assertEqual("eml-gbif", self.cases["synthetic"].findtext("kdbMetadataSchema"))
        self.assertEqual("1", self.cases["synthetic"].findtext("kdbIndexVersion"))
        self.assertEqual("researchSite", scalars["type"])
        self.assertEqual(["CSV", "tsv"], [field["value"] for field in fields if field["name"] == "format"])
        parties = json.loads(self.named(self.cases["synthetic"], "kdbParties")[0]["value"])
        self.assertEqual(parties, json.loads(self.cases["synthetic"].findtext("kdbParties")))
        self.assertEqual(["author", "pointOfContact", "principalInvestigator", "publisher"], [party["role"] for party in parties])
        self.assertEqual("Ana Novak", parties[0]["name"])
        self.assertEqual('ana"\\example.test', parties[0]["email"])
        self.assertEqual("", parties[2]["name"])
        self.assertTrue(all(party["website"] == "" for party in parties))
        identifiers = json.loads(self.named(self.cases["synthetic"], "kdbIdentifiers")[0]["value"])
        self.assertEqual(identifiers, json.loads(self.cases["synthetic"].findtext("kdbIdentifiers")))
        self.assertEqual(['local "identifier"\\one'], identifiers)
        links = json.loads(self.named(self.cases["synthetic"], "kdbLinks")[0]["value"])
        self.assertEqual(links, json.loads(self.cases["synthetic"].findtext("kdbLinks")))
        self.assertEqual(1, len(links))
        self.assertEqual("download", links[0]["function"])
        self.assertEqual('CSV "download"', links[0]["name"])
        boxes = json.loads(self.named(self.cases["synthetic"], "kdbBboxes")[0]["value"])
        self.assertEqual(boxes, json.loads(self.cases["synthetic"].findtext("kdbBboxes")))
        self.assertEqual([[14.123456, 45.1, 14.9, 45.8], [13.8, 45.0, 15.0, 46.0]], boxes)

    def test_all_migration_mefs_emit_complete_json_array_fields(self):
        mefs = sorted(MIGRATIONS.glob("*.mef"))
        self.assertEqual(17, len(mefs))
        self.assertEqual(18, len(self.cases))
        for package in mefs:
            with self.subTest(package=package.name):
                fields = self.fields(self.cases[package.name])
                scalars = {field["name"]: field["value"] for field in fields if field.get("type") != "object"}
                self.assertEqual("eml-gbif", scalars["kdbMetadataSchema"])
                self.assertEqual("1", scalars["kdbIndexVersion"])
                self.assertEqual("eml-gbif", self.cases[package.name].findtext("kdbMetadataSchema"))
                self.assertEqual("1", self.cases[package.name].findtext("kdbIndexVersion"))
                self.assertEqual(1, len(self.named(self.cases[package.name], "kdbParties")))
                self.assertEqual(1, len(self.named(self.cases[package.name], "kdbIdentifiers")))
                self.assertEqual(1, len(self.named(self.cases[package.name], "kdbLinks")))
                self.assertEqual(1, len(self.named(self.cases[package.name], "kdbBboxes")))
                for field_name in ("kdbParties", "kdbIdentifiers", "kdbLinks", "kdbBboxes"):
                    with self.subTest(field=field_name):
                        expected = json.loads(self.named(self.cases[package.name], field_name)[0]["value"])
                        self.assertIsInstance(expected, list)
                        self.assertEqual(expected, json.loads(self.cases[package.name].findtext(field_name)))

    def test_pollen_fallback_and_selected_source_cases(self):
        pollen = self.cases["pollen-eml-gbif.mef"]
        pollen_fields = self.fields(pollen)
        self.assertEqual("dataset", next(field["value"] for field in pollen_fields if field["name"] == "type"))
        self.assertEqual(["csv"], [field["value"] for field in pollen_fields if field["name"] == "format"])

        pathogens = json.loads(self.named(self.cases["skocjan-detected-pathogens-eml-gbif.mef"], "kdbParties")[0]["value"])
        self.assertIn("publisher", [party["role"] for party in pathogens])

        marine = mef_eml(MIGRATIONS / "marine-phytoplankton-database-eml-gbif.mef")
        self.assertTrue(any(local_name(node) == "abstract" for node in marine.iter()))


if __name__ == "__main__":
    unittest.main()
