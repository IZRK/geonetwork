"""Convert the supplied Karst microbiological database MEF to EML-GBIF."""

import csv
import io
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import sys
from urllib.parse import quote
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


UUID = "28b6a390-8254-479b-ba55-c70f59e121d6"
GMD = "http://www.isotc211.org/2005/gmd"
GCO = "http://www.isotc211.org/2005/gco"
EML = "https://eml.ecoinformatics.org/eml-2.2.0"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS = {"gmd": GMD, "gco": GCO}
ET.register_namespace("eml", EML)
ET.register_namespace("xsi", XSI)


def source_text(node, path):
    return (node.findtext(path, namespaces=NS) or "").strip()


def add(parent, name, value=None):
    child = ET.SubElement(parent, name)
    child.text = value
    return child


def add_person(parent, name, organization, email):
    given, surname = name.rsplit(" ", 1)
    individual = add(parent, "individualName")
    add(individual, "givenName", given)
    add(individual, "surName", surname)
    add(parent, "organizationName", organization)
    add(parent, "electronicMailAddress", email)


def build(source_dir, output):
    record_dir = source_dir / UUID
    iso = ET.parse(record_dir / "metadata/metadata.xml").getroot()
    info = ET.parse(record_dir / "info.xml").getroot()
    if (source_text(iso, "gmd:fileIdentifier/gco:CharacterString") != UUID
            or info.findtext("general/uuid") != UUID):
        raise ValueError("The ISO and MEF UUIDs must match the expected record")

    title = source_text(iso, ".//gmd:CI_Citation/gmd:title/gco:CharacterString")
    abstract = source_text(iso, ".//gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString")
    keywords = [node.text for node in iso.findall(
        ".//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString", NS)]
    party = iso.find(".//gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty", NS)
    name = source_text(party, "gmd:individualName/gco:CharacterString")
    organization = source_text(party, "gmd:organisationName/gco:CharacterString")
    email = source_text(party, ".//gmd:electronicMailAddress/gco:CharacterString")
    role = party.find("gmd:role/gmd:CI_RoleCode", NS).get("codeListValue")
    scope = iso.find("gmd:hierarchyLevel/gmd:MD_ScopeCode", NS).get("codeListValue")
    status = iso.find(".//gmd:status/gmd:MD_ProgressCode", NS).get("codeListValue")
    bounds = iso.find(".//gmd:EX_GeographicBoundingBox", NS)
    images = list((record_dir / "public").iterdir())
    if not all((title, abstract, name, organization, email)) or bounds is None or len(images) != 1:
        raise ValueError("Required source fields or the single public image are missing")
    if "Slovenia" not in keywords or "created in 2017 at the Karst Research Institute ZRC SAZU" not in abstract:
        raise ValueError("Source support for the required EML description or creator is missing")
    if source_text(iso, ".//gmd:CI_Date/gmd:date/gco:Date"):
        raise ValueError("Review a populated citation date before assigning EML pubDate")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    eml = ET.Element(f"{{{EML}}}eml", {
        "packageId": UUID,
        "system": "https://metadata.izrk.zrc-sazu.si",
        "scope": "system",
        f"{{{XSI}}}schemaLocation":
            "https://eml.ecoinformatics.org/eml-2.2.0 "
            "https://metadatacatalogue.lifewatch.eu/xml/schemas/eml-gbif/schema/eml.xsd",
        "{http://www.w3.org/XML/1998/namespace}lang": "en",
    })
    dataset = add(eml, "dataset")
    add(dataset, "alternateIdentifier", UUID)
    add(dataset, "title", title)
    # The abstract says the database was created at this institute; it does not
    # identify the named custodian as its creator.
    add(add(dataset, "creator"), "organizationName", organization)
    custodian = add(dataset, "associatedParty")
    add_person(custodian, name, organization, email)
    add(custodian, "role", role)
    add(dataset, "language", "eng")
    abstract_node = add(dataset, "abstract")
    for paragraph in abstract.split("\n\n"):
        add(abstract_node, "para", paragraph.strip())
    keyword_set = add(dataset, "keywordSet")
    for keyword in keywords:
        add(keyword_set, "keyword", keyword)
    add(add(dataset, "additionalInfo"), "para", "ISO hierarchy level: " + scope + "\nISO status: " + status)
    coverage = add(dataset, "coverage")
    geographic = add(coverage, "geographicCoverage")
    add(geographic, "geographicDescription", "Slovenia")
    coordinates = add(geographic, "boundingCoordinates")
    for source_name, target_name in (
        ("westBoundLongitude", "westBoundingCoordinate"),
        ("eastBoundLongitude", "eastBoundingCoordinate"),
        ("northBoundLatitude", "northBoundingCoordinate"),
        ("southBoundLatitude", "southBoundingCoordinate"),
    ):
        add(coordinates, target_name, source_text(bounds, f"gmd:{source_name}/gco:Decimal"))
    add_person(add(dataset, "contact"), name, organization, email)
    gbif = add(add(add(eml, "additionalMetadata"), "metadata"), "gbif")
    add(gbif, "dateStamp", now)
    add(gbif, "hierarchyLevel", scope)
    add(gbif, "resourceLogoUrl", quote(images[0].name))
    ET.indent(eml)

    general = info.find("general")
    general.find("schema").text = "eml-gbif"
    general.find("changeDate").text = now
    for name in ("localId", "siteId", "siteName", "rating", "popularity"):
        node = general.find(name)
        if node is not None:
            general.remove(node)
    ET.indent(info)

    index = io.StringIO(newline="")
    writer = csv.writer(index, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow(("schema", "uuid", "id", "type", "isHarvested", "title", "abstract"))
    writer.writerow(("eml-gbif", UUID, "", "METADATA", "false", title, abstract))
    html = ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<title>Export Index</title><body><h1>" + escape(title) + "</h1>"
            "<p>UUID: " + UUID + "</p><p>Schema: eml-gbif</p></body></html>")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", ZIP_DEFLATED) as archive:
        archive.writestr("index.csv", index.getvalue())
        archive.writestr("index.html", html)
        archive.writestr(f"{UUID}/info.xml", ET.tostring(info, encoding="utf-8", xml_declaration=True))
        archive.writestr(f"{UUID}/metadata/metadata.xml",
                         ET.tostring(eml, encoding="utf-8", xml_declaration=True))
        archive.write(images[0], f"{UUID}/public/{images[0].name}")


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
