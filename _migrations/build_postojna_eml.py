"""Build the EML-GBIF MEF for the supplied Postojna Cave ISO export."""

import csv
import io
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import sys
from urllib.parse import quote
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


GMD = "http://www.isotc211.org/2005/gmd"
GCO = "http://www.isotc211.org/2005/gco"
EML = "https://eml.ecoinformatics.org/eml-2.2.0"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS = {"gmd": GMD, "gco": GCO}
ET.register_namespace("eml", EML)
ET.register_namespace("xsi", XSI)


def source_text(node, path):
    value = node.findtext(path, namespaces=NS)
    return value.strip() if value else ""


def add(parent, name, value=None):
    element = ET.SubElement(parent, name)
    element.text = value
    return element


def build(source_dir, output):
    record_dir = next(path for path in source_dir.iterdir() if path.is_dir())
    uuid = record_dir.name
    iso = ET.parse(record_dir / "metadata/metadata.xml").getroot()
    source_info = ET.parse(record_dir / "info.xml").getroot()
    assert source_text(iso, "gmd:fileIdentifier/gco:CharacterString") == uuid
    assert source_info.findtext("general/uuid") == uuid

    title = source_text(iso, ".//gmd:CI_Citation/gmd:title/gco:CharacterString")
    abstract = source_text(iso, ".//gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString")
    keywords = [node.text for node in iso.findall(
        ".//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString", NS)]
    owner = iso.find(".//gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty", NS)
    name = source_text(owner, "gmd:individualName/gco:CharacterString")
    organization = source_text(owner, "gmd:organisationName/gco:CharacterString")
    email = source_text(owner, ".//gmd:electronicMailAddress/gco:CharacterString")
    assert name and organization and email
    metadata_email = source_text(iso, "gmd:contact/gmd:CI_ResponsibleParty/.//gmd:electronicMailAddress/gco:CharacterString")
    extent = iso.find(".//gmd:EX_Extent", NS)
    bounds = extent.find("gmd:geographicElement/gmd:EX_GeographicBoundingBox", NS)
    image = next(iter((record_dir / "public").iterdir()))
    assert len(list((record_dir / "public").iterdir())) == 1
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    eml = ET.Element(f"{{{EML}}}eml", {
        "packageId": uuid,
        "system": "https://metadata.izrk.zrc-sazu.si",
        "scope": "system",
        f"{{{XSI}}}schemaLocation":
            "https://eml.ecoinformatics.org/eml-2.2.0 "
            "https://metadatacatalogue.lifewatch.eu/xml/schemas/eml-gbif/schema/eml.xsd",
        "{http://www.w3.org/XML/1998/namespace}lang": "en",
    })
    dataset = add(eml, "dataset")
    add(dataset, "alternateIdentifier", uuid)
    add(dataset, "title", title)
    given, surname = name.rsplit(" ", 1)
    creator = add(dataset, "creator")
    personal = add(creator, "individualName")
    add(personal, "givenName", given)
    add(personal, "surName", surname)
    add(creator, "organizationName", organization)
    add(creator, "electronicMailAddress", email)
    # The data owner supplied this name; the source ISO contact has only an email.
    assert metadata_email == "magdalena.aljancic@zrc-sazu.si"
    metadata_provider = add(dataset, "metadataProvider")
    provider_name = add(metadata_provider, "individualName")
    add(provider_name, "givenName", "Magdalena")
    add(provider_name, "surName", "Aljančič")
    add(metadata_provider, "electronicMailAddress", metadata_email)
    # The citation date has type "creation", so there is no EML pubDate.
    heading, citations = abstract.split("\n", 1)
    paragraphs = [heading] + [part.strip() for part in citations.split("\n\n")]
    abstract_node = add(dataset, "abstract")
    for paragraph in paragraphs:
        add(abstract_node, "para", paragraph)
    keyword_set = add(dataset, "keywordSet")
    for keyword in keywords:
        add(keyword_set, "keyword", keyword)

    residual = [
        "ISO citation date (creation): " + source_text(iso, ".//gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date"),
        "ISO parent identifier: " + source_text(iso, "gmd:parentIdentifier/gco:CharacterString"),
        "ISO hierarchy level: " + iso.find("gmd:hierarchyLevel/gmd:MD_ScopeCode", NS).get("codeListValue"),
        "ISO status: " + iso.find(".//gmd:status/gmd:MD_ProgressCode", NS).get("codeListValue"),
        "ISO aggregation (largerWorkCitation): " + source_text(iso, ".//gmd:aggregateDataSetIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString"),
    ]
    add(add(dataset, "additionalInfo"), "para", "\n".join(residual))
    coverage = add(dataset, "coverage")
    geographic = add(coverage, "geographicCoverage")
    add(geographic, "geographicDescription", source_text(extent, "gmd:description/gco:CharacterString"))
    bounding = add(geographic, "boundingCoordinates")
    for source_name, target_name in (
        ("westBoundLongitude", "westBoundingCoordinate"),
        ("eastBoundLongitude", "eastBoundingCoordinate"),
        ("northBoundLatitude", "northBoundingCoordinate"),
        ("southBoundLatitude", "southBoundingCoordinate"),
    ):
        add(bounding, target_name, source_text(bounds, f"gmd:{source_name}/gco:Decimal"))
    contact = add(dataset, "contact")
    personal = add(contact, "individualName")
    add(personal, "givenName", given)
    add(personal, "surName", surname)
    add(contact, "organizationName", organization)
    add(contact, "electronicMailAddress", email)
    gbif = add(add(add(eml, "additionalMetadata"), "metadata"), "gbif")
    add(gbif, "dateStamp", now)
    add(gbif, "hierarchyLevel", "Research sites")
    add(gbif, "resourceLogoUrl", quote(image.name))
    ET.indent(eml)
    metadata = ET.tostring(eml, encoding="utf-8", xml_declaration=True)

    general = source_info.find("general")
    general.find("schema").text = "eml-gbif"
    general.find("changeDate").text = now
    for name in ("localId", "siteId", "siteName", "rating", "popularity"):
        node = general.find(name)
        if node is not None:
            general.remove(node)
    ET.indent(source_info)
    info = ET.tostring(source_info, encoding="utf-8", xml_declaration=True)

    index = io.StringIO(newline="")
    writer = csv.writer(index, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow(("schema", "uuid", "id", "type", "isHarvested", "title", "abstract"))
    writer.writerow(("eml-gbif", uuid, "", "METADATA", "false", title, abstract))
    html = ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<title>Export Index</title><body><h1>" + escape(title) + "</h1>"
            "<p>UUID: " + escape(uuid) + "</p><p>Schema: eml-gbif</p></body></html>")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", ZIP_DEFLATED) as archive:
        archive.writestr("index.csv", index.getvalue())
        archive.writestr("index.html", html)
        archive.writestr(f"{uuid}/info.xml", info)
        archive.writestr(f"{uuid}/metadata/metadata.xml", metadata)
        archive.write(image, f"{uuid}/public/{image.name}")


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
