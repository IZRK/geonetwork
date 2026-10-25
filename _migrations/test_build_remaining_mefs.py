"""Independent source-to-target checks for the nine new migration packages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from urllib.parse import quote, unquote, urlparse
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from build_remaining_mefs import CORRECTED_PARTY_NAMES, RECORDS, ROOT


NS = {"gmd": "http://www.isotc211.org/2005/gmd", "gco": "http://www.isotc211.org/2005/gco"}
XSD = ROOT.parent / "schemas/eml-gbif/src/main/plugin/eml-gbif/schema/eml.xsd"
INDEX_XSL = ROOT.parent / "schemas/eml-gbif/src/main/plugin/eml-gbif/index-fields/index.xsl"
WAR_LIB = ROOT.parent / "web/target/geonetwork/WEB-INF/lib"


def texts(root: ET.Element, path: str, ns: dict[str, str] | None = None) -> list[str]:
    return [node.text.strip() for node in root.findall(path, ns or {}) if node.text and node.text.strip()]


class MigrationPackagesTest(unittest.TestCase):
    def test_every_package_preserves_source_record_and_access(self):
        for uuid, slug in RECORDS.items():
            with self.subTest(uuid=uuid), ZipFile(ROOT / "source-exports" / f"{uuid}.zip") as source, \
                    ZipFile(ROOT / f"{slug}-eml-gbif.mef") as target:
                source_files = {name: source.read(name) for name in source.namelist() if not name.endswith("/")}
                target_files = {name: target.read(name) for name in target.namelist() if not name.endswith("/")}
                iso = ET.fromstring(source_files[f"{uuid}/metadata/metadata.xml"])
                eml = ET.fromstring(target_files[f"{uuid}/metadata/metadata.xml"])
                source_info = ET.fromstring(source_files[f"{uuid}/info.xml"])
                target_info = ET.fromstring(target_files[f"{uuid}/info.xml"])

                self.assertEqual(uuid, eml.get("packageId"))
                self.assertEqual(uuid, eml.findtext("dataset/alternateIdentifier"))
                self.assertEqual(uuid, target_info.findtext("general/uuid"))
                self.assertEqual("eml-gbif", target_info.findtext("general/schema"))
                self.assertEqual(source_info.findtext("general/createDate"), target_info.findtext("general/createDate"))
                for forbidden in ("localId", "siteId", "siteName", "rating", "popularity"):
                    self.assertIsNone(target_info.find(f"general/{forbidden}"))
                for section in ("categories", "privileges"):
                    self.assertEqual(ET.tostring(source_info.find(section)), ET.tostring(target_info.find(section)))

                source_title = texts(iso, ".//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString", NS)
                source_abstract = texts(iso, ".//gmd:identificationInfo//gmd:abstract/gco:CharacterString", NS)
                source_keywords = texts(iso, ".//gmd:descriptiveKeywords//gmd:keyword/gco:CharacterString", NS)
                self.assertEqual(source_title, texts(eml, "dataset/title"))
                target_abstract = texts(eml, "dataset/abstract/para")
                source_abstract_text = source_abstract[0] if source_abstract else "No abstract was provided in the source ISO metadata."
                self.assertEqual(" ".join(source_abstract_text.split()), " ".join(" ".join(target_abstract).split()))
                self.assertEqual(source_keywords, texts(eml, "dataset/keywordSet/keyword"))

                for scope in ("public", "private"):
                    source_manifest = {node.get("name"): node.get("changeDate")
                                       for node in source_info.findall(f"{scope}/file")}
                    target_manifest = {node.get("name"): node.get("changeDate")
                                       for node in target_info.findall(f"{scope}/file")}
                    self.assertEqual(source_manifest, target_manifest)
                    manifest = set(target_manifest)
                    actual = {name.split(f"{uuid}/{scope}/", 1)[1] for name in target_files
                              if name.startswith(f"{uuid}/{scope}/")}
                    self.assertEqual(manifest, actual)
                    for name in actual:
                        path = f"{uuid}/{scope}/{name}"
                        self.assertEqual(hashlib.sha256(source_files[path]).digest(),
                                         hashlib.sha256(target_files[path]).digest())
                for bound, eml_bound in (("westBoundLongitude", "westBoundingCoordinate"),
                                         ("eastBoundLongitude", "eastBoundingCoordinate"),
                                         ("northBoundLatitude", "northBoundingCoordinate"),
                                         ("southBoundLatitude", "southBoundingCoordinate")):
                    source_value = texts(iso, f".//gmd:EX_GeographicBoundingBox/gmd:{bound}/gco:Decimal", NS)
                    target_value = texts(eml, f"dataset/coverage/geographicCoverage/boundingCoordinates/{eml_bound}")
                    self.assertEqual(source_value, target_value)

                source_links = texts(iso, ".//gmd:identificationInfo//gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL", NS)
                target_links = texts(eml, "dataset/distribution/online/url")
                self.assertTrue(set(source_links).issubset(target_links))
                source_images = [unquote(urlparse(url).path.rsplit("/", 1)[-1]) for url in
                                 texts(iso, ".//gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString", NS)]
                logo = texts(eml, "additionalMetadata/metadata/gbif/resourceLogoUrl")
                self.assertEqual([quote(source_images[0])] if source_images else [], logo)
                additional = texts(eml, "dataset/additionalInfo/para")
                for image in source_images[1:]:
                    self.assertIn("ISO additional browse image: " + quote(image), additional[0])
                self.assertEqual(len(source_keywords), len(texts(eml, "dataset/keywordSet/keyword")))
                source_roles = []
                for party in iso.findall(".//gmd:CI_ResponsibleParty", NS):
                    name = texts(party, "gmd:individualName/gco:CharacterString", NS)
                    organization = texts(party, "gmd:organisationName/gco:CharacterString", NS)
                    email = texts(party, ".//gmd:electronicMailAddress/gco:CharacterString", NS)
                    role = party.find("gmd:role/gmd:CI_RoleCode", NS)
                    if (name or organization) and role is not None and role.get("codeListValue"):
                        original_name = name[0] if name else ""
                        corrected_name = CORRECTED_PARTY_NAMES.get(uuid, {}).get(original_name, original_name)
                        source_roles.append((corrected_name, organization[0] if organization else "",
                                             email[0] if email else "", role.get("codeListValue")))
                target_roles = []
                for party in eml.findall("dataset/associatedParty"):
                    name = " ".join(texts(party, "individualName/givenName") + texts(party, "individualName/surName"))
                    target_roles.append((name, party.findtext("organizationName") or "",
                                         party.findtext("electronicMailAddress") or "", party.findtext("role") or ""))
                self.assertEqual(set(source_roles), set(target_roles))
                self.assertIn("eml-gbif", target_files["index.csv"].decode())
                self.assertNotIn("iso19139", target_files["index.csv"].decode())

    def test_flo_veg_si_party_names_are_corrected_from_authoritative_sources(self):
        uuid = "9a5a0578-f6c5-4c44-9ca6-e23baada5ffb"
        with ZipFile(ROOT / "flovegsi-database-eml-gbif.mef") as archive:
            eml = ET.fromstring(archive.read(f"{uuid}/metadata/metadata.xml"))
        names = [" ".join(texts(party, "individualName/givenName") + texts(party, "individualName/surName"))
                 for party in eml.findall("dataset/associatedParty")]
        self.assertIn("Andrej Seliškar", names)
        self.assertIn("Tomaž Seliškar", names)
        self.assertNotIn("Andrej Seliökar", names)
        self.assertNotIn("Tomaû Seliökar", names)

    def test_pojs_publications_use_separate_abstract_paragraphs(self):
        uuid = "ce4ccbc2-ebba-43d7-af35-8aee7e6f7935"
        with ZipFile(ROOT / "postojna-pojs-minisite-eml-gbif.mef") as archive:
            eml = ET.fromstring(archive.read(f"{uuid}/metadata/metadata.xml"))
        paragraphs = texts(eml, "dataset/abstract/para")
        self.assertEqual("Related publications:", paragraphs[0])
        self.assertGreater(len(paragraphs), 10)
        self.assertTrue(all(paragraph.strip() for paragraph in paragraphs))

    def test_all_generated_metadata_validate_against_local_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            for uuid, slug in RECORDS.items():
                with self.subTest(uuid=uuid), ZipFile(ROOT / f"{slug}-eml-gbif.mef") as archive:
                    xml = Path(directory) / f"{uuid}.xml"
                    xml.write_bytes(archive.read(f"{uuid}/metadata/metadata.xml"))
                    result = subprocess.run(["xmllint", "--nonet", "--noout", "--schema", str(XSD), str(xml)],
                                            capture_output=True, text=True)
                    self.assertEqual(0, result.returncode, result.stderr)

    def test_index_transform_emits_every_source_keyword(self):
        # GeoNetwork's XslUtil expects a running Spring context. This narrow
        # test shim supplies only the URL setting and JSON escaping; the real
        # index stylesheet and the generated MEF metadata are still executed.
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            java = directory / "org/fao/geonet/util/XslUtil.java"
            java.parent.mkdir(parents=True)
            java.write_text(r'''package org.fao.geonet.util;
public final class XslUtil {
  public static String getSettingValue(String key) { return "https://metadata.izrk.zrc-sazu.si/srv/"; }
  public static String escapeForJson(String value) {
    if (value == null) return "";
    return value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
  }
}''', encoding="utf-8")
            subprocess.run(["javac", str(java)], check=True, capture_output=True, text=True)
            classpath = f"{directory}:{WAR_LIB}/*"
            for uuid, slug in RECORDS.items():
                with self.subTest(uuid=uuid), ZipFile(ROOT / f"{slug}-eml-gbif.mef") as archive:
                    xml = directory / f"{uuid}.xml"
                    indexed = directory / f"{uuid}-index.xml"
                    xml.write_bytes(archive.read(f"{uuid}/metadata/metadata.xml"))
                    result = subprocess.run(["java", "-cp", classpath, "net.sf.saxon.Transform",
                                             f"-s:{xml}", f"-xsl:{INDEX_XSL}", f"-o:{indexed}"],
                                            capture_output=True, text=True)
                    self.assertEqual(0, result.returncode, result.stderr)
                    eml = ET.parse(xml).getroot()
                    output = ET.parse(indexed).getroot()
                    expected = texts(eml, "dataset/keywordSet/keyword")
                    tag = json.loads(output.findtext("tag"))
                    all_keywords = json.loads(output.findtext("allKeywords"))["otherKeywords-theme"]["keywords"]
                    self.assertEqual(expected, [item["default"] for item in tag])
                    self.assertEqual(expected, [item["default"] for item in all_keywords])
                    self.assertEqual(len(expected), int(output.findtext("tagNumber")))
                    with ZipFile(ROOT / "source-exports" / f"{uuid}.zip") as source:
                        iso = ET.fromstring(source.read(f"{uuid}/metadata/metadata.xml"))
                    expected_images = len(iso.findall(".//gmd:MD_BrowseGraphic", NS))
                    self.assertEqual(expected_images, len(output.findall("overview")))


if __name__ == "__main__":
    unittest.main()
