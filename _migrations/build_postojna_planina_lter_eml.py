"""Build an EML-GBIF MEF for the Postojna-Planina LTER research site."""

from __future__ import annotations

import argparse
import csv
import io
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


UUID = "d3011b1e-3aa5-4b61-a3bc-94da67f582c8"
DEFAULT_SOURCE = Path("/Users/vids/Downloads") / UUID
DEFAULT_OUTPUT = Path(__file__).with_name("postojna-planina-lter-eml-gbif.mef")
GMD = "http://www.isotc211.org/2005/gmd"
GCO = "http://www.isotc211.org/2005/gco"
EML = "https://eml.ecoinformatics.org/eml-2.2.0"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS = {"gmd": GMD, "gco": GCO}


def source_text(node: ET.Element, path: str) -> str:
    value = node.findtext(path, namespaces=NS)
    return value.strip() if value else ""


def add(parent: ET.Element, name: str, value: str | None = None) -> ET.Element:
    child = ET.SubElement(parent, name)
    child.text = value
    return child


def add_person(parent: ET.Element, kind: str, source: ET.Element) -> ET.Element:
    person = add(parent, kind)
    name = source_text(source, "gmd:individualName/gco:CharacterString")
    if name:
        given, surname = name.rsplit(" ", 1)
        individual = add(person, "individualName")
        add(individual, "givenName", given)
        add(individual, "surName", surname)
    organization = source_text(source, "gmd:organisationName/gco:CharacterString")
    if organization:
        add(person, "organizationName", organization)
    email = source_text(source, ".//gmd:electronicMailAddress/gco:CharacterString")
    if email:
        add(person, "electronicMailAddress", email)
    return person


def build(source: Path, output: Path) -> None:
    record = source / UUID
    iso = ET.parse(record / "metadata/metadata.xml").getroot()
    info = ET.parse(record / "info.xml").getroot()
    assert source_text(iso, "gmd:fileIdentifier/gco:CharacterString") == UUID
    assert info.findtext("general/schema") == "iso19139"
    assert info.findtext("general/uuid") == UUID

    title = source_text(iso, ".//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString")
    abstract = source_text(iso, ".//gmd:identificationInfo//gmd:abstract/gco:CharacterString")
    paragraphs = [line.strip() for line in abstract.splitlines() if line.strip()]
    assert " ".join(" ".join(paragraphs).split()) == " ".join(abstract.split())
    keywords = [node.text.strip() for node in iso.findall(
        ".//gmd:descriptiveKeywords//gmd:keyword/gco:CharacterString", NS)]
    parties = iso.findall(".//gmd:identificationInfo//gmd:pointOfContact/gmd:CI_ResponsibleParty", NS)
    assert len(parties) == 2
    assert [party.find("gmd:role/gmd:CI_RoleCode", NS).get("codeListValue") for party in parties] == [
        "custodian", "pointOfContact"]
    scope = iso.find("gmd:hierarchyLevel/gmd:MD_ScopeCode", NS).get("codeListValue")
    status = iso.find(".//gmd:status/gmd:MD_ProgressCode", NS).get("codeListValue")
    language = iso.find("gmd:language/gmd:LanguageCode", NS).get("codeListValue")
    citation_date = source_text(iso, ".//gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date")
    assert citation_date == ""
    browse_urls = [node.text.strip() for node in iso.findall(
        ".//gmd:graphicOverview//gmd:fileName/gco:CharacterString", NS)]
    assert len(browse_urls) == 3
    browse_names = [unquote(Path(urlparse(url).path).name) for url in browse_urls]
    manifest_names = {item.attrib["name"] for item in info.findall("public/file")}
    actual_names = {path.name for path in (record / "public").iterdir() if path.is_file()}
    assert manifest_names == actual_names == set(browse_names)
    assert not list((record / "private").iterdir())

    deims_lines = [line for line in paragraphs if line.startswith("DEIMS: ")]
    assert len(deims_lines) == 1
    deims_url = deims_lines[0].removeprefix("DEIMS: ")
    assert deims_url.startswith("https://deims.org/")

    ET.register_namespace("eml", EML)
    ET.register_namespace("xsi", XSI)
    eml = ET.Element(f"{{{EML}}}eml", {
        "packageId": UUID,
        "system": "https://metadata.izrk.zrc-sazu.si",
        "scope": "system",
        f"{{{XSI}}}schemaLocation":
            f"{EML} https://metadatacatalogue.lifewatch.eu/xml/schemas/eml-gbif/schema/eml.xsd",
        "{http://www.w3.org/XML/1998/namespace}lang": "en",
    })
    dataset = add(eml, "dataset")
    add(dataset, "alternateIdentifier", UUID)
    add(dataset, "title", title)
    # The source names an operating organization, but no creator. The local
    # EML-GBIF profile requires one; preserve the organization as that party.
    add(add(dataset, "creator"), "organizationName",
        source_text(parties[0], "gmd:organisationName/gco:CharacterString"))
    add(add_person(dataset, "associatedParty", parties[0]), "role", "custodian")
    abstract_node = add(dataset, "abstract")
    for paragraph in paragraphs:
        add(abstract_node, "para", paragraph)
    keyword_set = add(dataset, "keywordSet")
    for keyword in keywords:
        add(keyword_set, "keyword", keyword)

    extra = [f"ISO hierarchy level: {scope}", f"ISO status: {status}",
             f"ISO metadata language: {language}"]
    extra.extend(f"ISO additional browse image: {quote(name)}" for name in browse_names[1:])
    add(add(dataset, "additionalInfo"), "para", "\n".join(extra))

    online = add(add(dataset, "distribution"), "online")
    add(online, "onlineDescription", "DEIMS site record")
    add(online, "url", deims_url)

    coverage = add(dataset, "coverage")
    geographic = add(coverage, "geographicCoverage")
    add(geographic, "geographicDescription",
        source_text(iso, ".//gmd:extent//gmd:description/gco:CharacterString"))
    bounds = add(geographic, "boundingCoordinates")
    source_bounds = iso.find(".//gmd:EX_GeographicBoundingBox", NS)
    for target, source_name in (
        ("westBoundingCoordinate", "westBoundLongitude"),
        ("eastBoundingCoordinate", "eastBoundLongitude"),
        ("northBoundingCoordinate", "northBoundLatitude"),
        ("southBoundingCoordinate", "southBoundLatitude"),
    ):
        add(bounds, target, source_text(source_bounds, f"gmd:{source_name}/gco:Decimal"))
    add_person(dataset, "contact", parties[1])

    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    gbif = add(add(add(eml, "additionalMetadata"), "metadata"), "gbif")
    add(gbif, "dateStamp", now)
    add(gbif, "hierarchyLevel", scope)
    add(gbif, "resourceLogoUrl", quote(browse_names[0]))
    ET.indent(eml, space="  ")
    metadata = ET.tostring(eml, encoding="utf-8", xml_declaration=True)

    general = info.find("general")
    general.find("schema").text = "eml-gbif"
    general.find("changeDate").text = now
    for obsolete in ("localId", "siteId", "siteName", "rating", "popularity"):
        item = general.find(obsolete)
        if item is not None:
            general.remove(item)
    ET.indent(info, space="  ")
    converted_info = ET.tostring(info, encoding="utf-8", xml_declaration=True)

    index = io.StringIO(newline="")
    writer = csv.writer(index, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow(("schema", "uuid", "id", "type", "isHarvested", "title", "abstract"))
    writer.writerow(("eml-gbif", UUID, "", "METADATA", "false", title, abstract))
    index_html = ("<!doctype html><html lang='en'><meta charset='utf-8'>"
                  "<title>Export Index</title><body><h1>" + escape(title) + "</h1>"
                  "<p>UUID: " + escape(UUID) + "</p><p>Schema: eml-gbif</p></body></html>")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("index.csv", index.getvalue())
        archive.writestr("index.html", index_html)
        archive.writestr(f"{UUID}/info.xml", converted_info)
        archive.writestr(f"{UUID}/metadata/metadata.xml", metadata)
        for name in sorted(manifest_names):
            archive.write(record / "public" / name, f"{UUID}/public/{name}")
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.source, args.output)
