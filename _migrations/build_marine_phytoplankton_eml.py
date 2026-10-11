"""Build an EML-GBIF MEF preserving the Marine phytoplankton database record."""

from __future__ import annotations

import argparse
import csv
import io
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


UUID = "1f7b7000-1cc3-428f-974d-a688398f51e0"
DEFAULT_SOURCE = Path("/Users/vids/Downloads") / UUID
DEFAULT_OUTPUT = Path(__file__).with_name("marine-phytoplankton-database-eml-gbif.mef")
GMD = "http://www.isotc211.org/2005/gmd"
GCO = "http://www.isotc211.org/2005/gco"
EML = "https://eml.ecoinformatics.org/eml-2.2.0"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS = {"gmd": GMD, "gco": GCO}
NO_ABSTRACT = "No abstract was provided in the source ISO metadata."

ET.register_namespace("eml", EML)
ET.register_namespace("xsi", XSI)


def source_text(node: ET.Element, path: str) -> str:
    value = node.findtext(path, namespaces=NS)
    return value.strip() if value else ""


def add(parent: ET.Element, name: str, value: str | None = None) -> ET.Element:
    child = ET.SubElement(parent, name)
    child.text = value
    return child


def build(source: Path, output: Path) -> dict[str, str]:
    record = source / UUID
    iso = ET.parse(record / "metadata/metadata.xml").getroot()
    info = ET.parse(record / "info.xml").getroot()
    if source_text(iso, "gmd:fileIdentifier/gco:CharacterString") != UUID:
        raise ValueError("The ISO metadata UUID does not match the expected record")
    if info.findtext("general/schema") != "iso19139" or info.findtext("general/uuid") != UUID:
        raise ValueError("The source MEF schema or UUID is unexpected")

    title = source_text(iso, ".//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString")
    abstract = source_text(iso, ".//gmd:identificationInfo//gmd:abstract/gco:CharacterString")
    keywords = [item.text.strip() for item in iso.findall(
        ".//gmd:descriptiveKeywords//gmd:keyword/gco:CharacterString", NS) if item.text]
    parties = iso.findall(".//gmd:identificationInfo//gmd:pointOfContact/gmd:CI_ResponsibleParty", NS)
    if not title or len(parties) != 1:
        raise ValueError("Expected a title and one source responsible party")
    party = parties[0]
    name = source_text(party, "gmd:individualName/gco:CharacterString")
    organization = source_text(party, "gmd:organisationName/gco:CharacterString")
    email = source_text(party, ".//gmd:electronicMailAddress/gco:CharacterString")
    role_node = party.find("gmd:role/gmd:CI_RoleCode", NS)
    role = role_node.get("codeListValue", "") if role_node is not None else ""
    scope_node = iso.find("gmd:hierarchyLevel/gmd:MD_ScopeCode", NS)
    scope = scope_node.get("codeListValue", "") if scope_node is not None else ""
    language_node = iso.find("gmd:language/gmd:LanguageCode", NS)
    language = language_node.get("codeListValue", "") if language_node is not None else ""
    bounds = iso.find(".//gmd:EX_GeographicBoundingBox", NS)
    if not all((name, organization, email, role, scope, language)) or bounds is None:
        raise ValueError("Expected contact, scope, language, and geographic bounds are missing")

    dates = []
    for date in iso.findall(".//gmd:CI_Citation/gmd:date/gmd:CI_Date", NS):
        value = source_text(date, "gmd:date/gco:Date") or source_text(date, "gmd:date/gco:DateTime")
        date_type = date.find("gmd:dateType/gmd:CI_DateTypeCode", NS)
        dates.append((date_type.get("codeListValue", "") if date_type is not None else "", value))
    if any(value and date_type == "publication" for date_type, value in dates):
        raise ValueError("Review a populated publication date before assigning EML pubDate")
    if abstract:
        raise ValueError("Review the source abstract before using the no-abstract placeholder")

    public_dir = record / "public"
    private_dir = record / "private"
    public_files = sorted(item for item in public_dir.iterdir() if item.is_file()) if public_dir.exists() else []
    private_files = sorted(item for item in private_dir.iterdir() if item.is_file()) if private_dir.exists() else []
    public_manifest = [item.get("name") for item in info.findall("public/file")]
    private_manifest = [item.get("name") for item in info.findall("private/file")]
    if public_manifest != [item.name for item in public_files] or private_manifest != [item.name for item in private_files]:
        raise ValueError("Source MEF attachment manifests do not match the extracted files")
    if public_files or private_files:
        raise ValueError("Review source attachments before running this attachment-free builder")
    if iso.findall(".//gmd:graphicOverview", NS):
        raise ValueError("Review source browse images before running this attachment-free builder")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
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
    # The source identifies the institute's party as custodian, not explicitly creator.
    add(add(dataset, "creator"), "organizationName", organization)
    associated = add(dataset, "associatedParty")
    individual = add(associated, "individualName")
    given, surname = name.rsplit(" ", 1)
    add(individual, "givenName", given)
    add(individual, "surName", surname)
    add(associated, "organizationName", organization)
    add(associated, "electronicMailAddress", email)
    add(associated, "role", role)
    add(dataset, "language", language)
    # The customized profile requires an abstract. This states only that the source omitted it.
    add(add(dataset, "abstract"), "para", NO_ABSTRACT)
    keyword_set = add(dataset, "keywordSet")
    for keyword in keywords:
        add(keyword_set, "keyword", keyword)

    geographic = add(add(dataset, "coverage"), "geographicCoverage")
    add(geographic, "geographicDescription", source_text(iso, ".//gmd:EX_Extent/gmd:description/gco:CharacterString"))
    coordinates = add(geographic, "boundingCoordinates")
    for target, source_name in (
        ("westBoundingCoordinate", "westBoundLongitude"),
        ("eastBoundingCoordinate", "eastBoundLongitude"),
        ("northBoundingCoordinate", "northBoundLatitude"),
        ("southBoundingCoordinate", "southBoundLatitude"),
    ):
        add(coordinates, target, source_text(bounds, f"gmd:{source_name}/gco:Decimal"))

    # EML requires a contact. Reuse the source custodian and record the role caveat above.
    contact = add(dataset, "contact")
    contact_name = add(contact, "individualName")
    add(contact_name, "givenName", given)
    add(contact_name, "surName", surname)
    add(contact, "organizationName", organization)
    add(contact, "electronicMailAddress", email)
    gbif = add(add(add(eml, "additionalMetadata"), "metadata"), "gbif")
    add(gbif, "dateStamp", now)
    add(gbif, "hierarchyLevel", scope)
    ET.indent(eml, space="  ")

    general = info.find("general")
    general.find("schema").text = "eml-gbif"
    general.find("changeDate").text = now
    for obsolete in ("localId", "siteId", "siteName", "rating", "popularity"):
        node = general.find(obsolete)
        if node is not None:
            general.remove(node)
    ET.indent(info, space="  ")

    index = io.StringIO(newline="")
    writer = csv.writer(index, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow(("schema", "uuid", "id", "type", "isHarvested", "title", "abstract"))
    writer.writerow(("eml-gbif", UUID, "", "METADATA", "false", title, NO_ABSTRACT))
    html = ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<title>Export Index</title><body><h1>" + escape(title) + "</h1>"
            "<p>UUID: " + UUID + "</p><p>Schema: eml-gbif</p></body></html>")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("index.csv", index.getvalue())
        archive.writestr("index.html", html)
        archive.writestr(f"{UUID}/info.xml", ET.tostring(info, encoding="utf-8", xml_declaration=True))
        archive.writestr(f"{UUID}/metadata/metadata.xml",
                         ET.tostring(eml, encoding="utf-8", xml_declaration=True))

    return {"title": title, "abstract": abstract, "keywords": " | ".join(keywords),
            "public_attachment_count": str(len(public_files)),
            "private_attachment_count": str(len(private_files)), "change_date": now}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build(args.source, args.output)
    print(args.output)
    print("Source public/private files: 0/0")
