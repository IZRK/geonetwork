"""Convert the reviewed ISO 19139 source exports to EML-GBIF MEFs.

The source ZIPs are kept in source-exports/ and are never modified. Run this
script from the repository root. The selected records are listed explicitly so
an unrelated export cannot be converted by accident.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
from pathlib import Path
import re
import unicodedata
from urllib.parse import quote, unquote, urlparse
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source-exports"
NS = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "eml": "https://eml.ecoinformatics.org/eml-2.2.0",
}
EML = NS["eml"]
XSI = "http://www.w3.org/2001/XMLSchema-instance"
MIGRATED_AT = "2026-10-24T07:30:00Z"
RECORDS = {
    "6006d62c-5143-4bbc-ad4c-9d9375b0f499": "skocjan-airborne-bacteria",
    "1b83ee14-6498-4f9b-a297-eb1692095c1a": "skocjan-detected-pathogens",
    "9a5a0578-f6c5-4c44-9ca6-e23baada5ffb": "flovegsi-database",
    "293dcc3b-8e9d-4c74-bfb2-67eddee69417": "institute-of-biology-herbarium",
    "2a1a1d63-9b2d-48d2-931d-b18945a580d5": "slovenian-bird-ringing-database",
    "b5c2c64a-325b-42d1-b5ad-2198ad434a55": "marine-genomic-arms-database",
    "aff1a1d3-46df-46df-a693-7d249134633c": "skocjan-caves-lter-site",
    "ce4ccbc2-ebba-43d7-af35-8aee7e6f7935": "postojna-pojs-minisite",
    "cec7e833-ef3c-443d-984b-5e0b15418375": "predjama-pr2-minisite",
}
REVIEW_NOTES = {
    "6006d62c-5143-4bbc-ad4c-9d9375b0f499": "The source describes Excel data but provides no data attachment or online data link.",
    "1b83ee14-6498-4f9b-a297-eb1692095c1a": "The source describes Excel data but provides no data attachment or online data link.",
    "b5c2c64a-325b-42d1-b5ad-2198ad434a55": "Conditional candidate: source has no abstract or data access link; confirm scope and access with the custodian before import.",
    "aff1a1d3-46df-46df-a693-7d249134633c": "Conditional candidate: research-site metadata, not an occurrence dataset; confirm GBIF publication scope with the owner.",
    "ce4ccbc2-ebba-43d7-af35-8aee7e6f7935": "Conditional candidate: research-site metadata and no data link; confirm GBIF publication scope with the owner.",
    "cec7e833-ef3c-443d-984b-5e0b15418375": "Conditional candidate: research-site metadata with no abstract or data link; correct the source title typo and confirm scope with the owner.",
}
# The FloVegSi export has mojibake in two author names. The intended spellings
# are confirmed by the official BIJH-hosted FloVegSi paper and ZRC/Cobiss
# records; keep the source export untouched and correct only the EML output.
CORRECTED_PARTY_NAMES = {
    "9a5a0578-f6c5-4c44-9ca6-e23baada5ffb": {
        "Andrej Seliökar": "Andrej Seliškar",
        "Tomaû Seliökar": "Tomaž Seliškar",
    },
}
ET.register_namespace("eml", EML)
ET.register_namespace("xsi", XSI)


def value(parent: ET.Element, path: str) -> str:
    node = parent.find(path, NS)
    return "" if node is None or node.text is None else node.text.strip()


def child(parent: ET.Element, name: str, text: str | None = None) -> ET.Element:
    node = ET.SubElement(parent, name)
    if text is not None:
        node.text = text
    return node


def code(parent: ET.Element, path: str) -> str:
    node = parent.find(path, NS)
    return "" if node is None else node.get("codeListValue", "")


def parties(iso: ET.Element) -> list[dict[str, str]]:
    result = []
    seen = set()
    for node in iso.findall(".//gmd:CI_ResponsibleParty", NS):
        party = {
            "name": value(node, "gmd:individualName/gco:CharacterString"),
            "organization": value(node, "gmd:organisationName/gco:CharacterString"),
            "position": value(node, "gmd:positionName/gco:CharacterString"),
            "email": value(node, ".//gmd:electronicMailAddress/gco:CharacterString"),
            "role": code(node, "gmd:role/gmd:CI_RoleCode"),
        }
        signature = tuple(party.values())
        if signature not in seen:
            seen.add(signature)
            result.append(party)
    return result


def agent(parent: ET.Element, tag: str, party: dict[str, str], role: bool = False) -> ET.Element:
    node = child(parent, tag)
    name = party["name"]
    if name:
        individual = child(node, "individualName")
        words = name.split()
        if len(words) > 1:
            child(individual, "givenName", " ".join(words[:-1]))
        child(individual, "surName", words[-1])
    if party["organization"]:
        child(node, "organizationName", party["organization"])
    if party["position"]:
        child(node, "positionName", party["position"])
    if party["email"]:
        child(node, "electronicMailAddress", party["email"])
    if role:
        child(node, "role", party["role"])
    return node


def norm(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def matching_file(filename: str, files: dict[str, bytes]) -> str:
    matches = [name for name in files if norm(name) == norm(filename)]
    if len(matches) != 1:
        raise ValueError(f"Attachment {filename!r} has {len(matches)} matches")
    return matches[0]


def source_record(uuid: str) -> tuple[ET.Element, ET.Element, dict[str, bytes]]:
    path = SOURCE / f"{uuid}.zip"
    with ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError(f"Corrupt source ZIP: {path}")
        files = {name: z.read(name) for name in z.namelist() if not name.endswith("/")}
    iso = ET.fromstring(files[f"{uuid}/metadata/metadata.xml"])
    info = ET.fromstring(files[f"{uuid}/info.xml"])
    if value(info, "general/schema") != "iso19139" or value(info, "general/uuid") != uuid:
        raise ValueError(f"Source identity mismatch: {uuid}")
    for scope in ("public", "private"):
        declared = {norm(item.get("name", "")) for item in info.findall(f"{scope}/file")}
        actual = {norm(name.rsplit("/", 1)[-1]) for name in files if name.startswith(f"{uuid}/{scope}/")}
        if declared != actual:
            raise ValueError(f"{uuid} {scope} manifest differs from source files: {declared ^ actual}")
    return iso, info, files


def build_eml(uuid: str, iso: ET.Element, files: dict[str, bytes]) -> tuple[bytes, dict]:
    title = value(iso, ".//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString")
    abstract = value(iso, ".//gmd:identificationInfo//gmd:abstract/gco:CharacterString")
    hierarchy = code(iso, ".//gmd:hierarchyLevel/gmd:MD_ScopeCode")
    status = code(iso, ".//gmd:identificationInfo//gmd:status/gmd:MD_ProgressCode")
    keywords = [node.text.strip() for node in iso.findall(".//gmd:descriptiveKeywords//gmd:keyword/gco:CharacterString", NS) if node.text and node.text.strip()]
    name_corrections = CORRECTED_PARTY_NAMES.get(uuid, {})
    people = parties(iso)
    for party in people:
        party["name"] = name_corrections.get(party["name"], party["name"])
    identified = [party for party in people if party["name"] or party["organization"] or party["position"]]
    if not identified:
        raise ValueError(f"No source-backed creator or contact: {uuid}")
    authors = [party for party in identified if party["role"] == "author"]
    creator_role_unconfirmed = not authors
    if authors:
        creators = authors
    else:
        fallback_role = next((role for role in ("owner", "custodian", "pointOfContact")
                              if any(party["role"] == role and party["name"] for party in identified)), None)
        if fallback_role:
            creators = [party for party in identified if party["role"] == fallback_role and party["name"]]
        else:
            source = next((party for party in identified if party["organization"]), identified[0])
            creators = [source]
    contacts = [party for party in identified if party["role"] == "pointOfContact"]
    if not contacts:
        contacts = [next((party for party in identified if party["email"]), identified[0])]

    root = ET.Element(f"{{{EML}}}eml", {
        "packageId": uuid, "system": "https://metadata.izrk.zrc-sazu.si", "scope": "system",
        f"{{{XSI}}}schemaLocation": f"{EML} https://metadatacatalogue.lifewatch.eu/xml/schemas/eml-gbif/schema/eml.xsd",
        "{http://www.w3.org/XML/1998/namespace}lang": "en",
    })
    dataset = child(root, "dataset")
    child(dataset, "alternateIdentifier", uuid)
    child(dataset, "title", title)
    for party in creators:
        agent(dataset, "creator", party)
    for party in identified:
        if party["role"]:
            agent(dataset, "associatedParty", party, role=True)
    for date in iso.findall(".//gmd:identificationInfo//gmd:citation//gmd:CI_Date", NS):
        if code(date, "gmd:dateType/gmd:CI_DateTypeCode") == "publication":
            publication = value(date, "gmd:date/gco:Date") or value(date, "gmd:date/gco:DateTime")
            if publication:
                child(dataset, "pubDate", publication[:10])
                break
    abstract_node = child(dataset, "abstract")
    if uuid == "ce4ccbc2-ebba-43d7-af35-8aee7e6f7935" and abstract.startswith("Related publications:"):
        # The source uses blank lines as citation boundaries. Preserve its
        # wording while letting the formatter display each citation as a
        # separate paragraph, like the Amphipoda record's references section.
        heading, _, citations = abstract.partition("\n")
        child(abstract_node, "para", heading.strip())
        for paragraph in re.split(r"\n\s*\n", citations):
            if paragraph.strip():
                child(abstract_node, "para", paragraph.strip())
    else:
        child(abstract_node, "para", abstract or "No abstract was provided in the source ISO metadata.")
    if keywords:
        keyset = child(dataset, "keywordSet")
        for keyword in keywords:
            child(keyset, "keyword", keyword)

    public_names = [name.rsplit("/", 1)[-1] for name in files if name.startswith(f"{uuid}/public/")]
    browse = []
    for graphic in iso.findall(".//gmd:MD_BrowseGraphic", NS):
        url = value(graphic, "gmd:fileName/gco:CharacterString")
        filename = unquote(urlparse(url).path.rsplit("/", 1)[-1])
        browse.append(matching_file(filename, {name: b"" for name in public_names}))
    notes = [f"ISO hierarchy level: {hierarchy}"] if hierarchy else []
    if status:
        notes.append(f"ISO status: {status}")
    language = code(iso, "gmd:language/gmd:LanguageCode") or value(iso, "gmd:language/gco:CharacterString")
    if language:
        notes.append(f"ISO metadata language: {language}")
    formats = []
    for source_format in iso.findall(".//gmd:distributionInfo//gmd:MD_Format", NS):
        format_name = value(source_format, "gmd:name/gco:CharacterString")
        if format_name:
            formats.append(format_name)
            notes.append(f"ISO distribution format: {format_name}")
    citation_dates = []
    for date in iso.findall(".//gmd:identificationInfo//gmd:citation//gmd:CI_Date", NS):
        date_text = value(date, "gmd:date/gco:Date") or value(date, "gmd:date/gco:DateTime")
        date_kind = code(date, "gmd:dateType/gmd:CI_DateTypeCode")
        if date_text and date_kind != "publication":
            citation_dates.append((date_kind, date_text))
            notes.append(f"ISO citation {date_kind} date: {date_text} (not a publication date)")
    # Keep role-mapping caveats in the preservation report, not in user-facing
    # Additional information. The source role and email remain represented in
    # the EML party/contact fields.
    for filename in browse[1:]:
        notes.append(f"ISO additional browse image: {quote(filename)}")
    if notes:
        child(child(dataset, "additionalInfo"), "para", "\n".join(notes))

    links = []
    for online in iso.findall(".//gmd:identificationInfo//gmd:onLine/gmd:CI_OnlineResource", NS):
        url = value(online, "gmd:linkage/gmd:URL")
        if not url:
            continue
        description = value(online, "gmd:description/gco:CharacterString") or value(online, "gmd:name/gco:CharacterString")
        if not description:
            description = unquote(urlparse(url).path.rsplit("/", 1)[-1]) or urlparse(url).netloc
        links.append((description, url))
    if hierarchy == "Research sites":
        for url in re.findall(r"https?://deims\.org/[0-9a-f-]{36}", abstract):
            if all(link != url for _, link in links):
                links.append(("DEIMS site record", url))
    for description, url in links:
        online = child(child(dataset, "distribution"), "online")
        child(online, "onlineDescription", description)
        child(online, "url", url)

    bounds = {}
    geographic_description = ""
    box = iso.find(".//gmd:EX_GeographicBoundingBox", NS)
    if box is not None:
        bounds = {key: value(box, f"gmd:{key}/gco:Decimal") for key in (
            "westBoundLongitude", "eastBoundLongitude", "northBoundLatitude", "southBoundLatitude")}
        if all(bounds.values()):
            coverage = child(dataset, "coverage")
            geo = child(coverage, "geographicCoverage")
            geographic_description = value(iso, ".//gmd:EX_Extent/gmd:description/gco:CharacterString") or "Source geographic bounding box"
            child(geo, "geographicDescription", geographic_description)
            coordinates = child(geo, "boundingCoordinates")
            for target, source in (("westBoundingCoordinate", "westBoundLongitude"),
                                   ("eastBoundingCoordinate", "eastBoundLongitude"),
                                   ("northBoundingCoordinate", "northBoundLatitude"),
                                   ("southBoundingCoordinate", "southBoundLatitude")):
                child(coordinates, target, bounds[source])
    for party in contacts:
        agent(dataset, "contact", party)
    publisher = next((party for party in identified if party["role"] == "publisher"), None)
    if publisher:
        agent(dataset, "publisher", publisher)

    gbif = child(child(child(root, "additionalMetadata"), "metadata"), "gbif")
    child(gbif, "dateStamp", MIGRATED_AT)
    if hierarchy:
        child(gbif, "hierarchyLevel", hierarchy)
    if browse:
        child(gbif, "resourceLogoUrl", quote(browse[0]))
    ET.indent(root, space="  ")
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml, {"title": title, "abstract": abstract, "keywords": keywords, "hierarchy": hierarchy,
                 "browse": browse, "links": links, "parties": people, "creator_role_unconfirmed": creator_role_unconfirmed,
                 "status": status, "language": language, "formats": formats, "bounds": bounds,
                 "geographic_description": geographic_description, "citation_dates": citation_dates}


def build_info(uuid: str, info: ET.Element, files: dict[str, bytes]) -> bytes:
    general = info.find("general")
    assert general is not None
    schema = general.find("schema")
    assert schema is not None
    schema.text = "eml-gbif"
    change = general.find("changeDate")
    assert change is not None
    change.text = MIGRATED_AT
    for field in ("localId", "siteId", "siteName", "rating", "popularity"):
        node = general.find(field)
        if node is not None:
            general.remove(node)
    for scope in ("public", "private"):
        manifest = info.find(scope)
        assert manifest is not None
        for item in manifest.findall("file"):
            name = item.get("name", "")
            actual = matching_file(name, {path.rsplit("/", 1)[-1]: b"" for path in files if path.startswith(f"{uuid}/{scope}/")})
            item.set("name", actual)
    ET.indent(info, space="  ")
    return ET.tostring(info, encoding="utf-8", xml_declaration=True)


def package(uuid: str, slug: str) -> Path:
    iso, info, files = source_record(uuid)
    eml, inventory = build_eml(uuid, iso, files)
    info_xml = build_info(uuid, info, files)
    out = ROOT / f"{slug}-eml-gbif.mef"
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(["schema", "uuid", "id", "type", "isHarvested", "title", "abstract"])
    writer.writerow(["eml-gbif", uuid, "", "METADATA", "false", inventory["title"], inventory["abstract"]])
    index_html = ("<!doctype html><html lang='en'><meta charset='utf-8'><title>Export Index</title>"
                  f"<body><h1>{html.escape(inventory['title'])}</h1><p>UUID: {uuid}</p>"
                  "<p>Schema: eml-gbif</p></body></html>")
    with ZipFile(out, "w", ZIP_DEFLATED) as z:
        z.writestr("index.csv", buffer.getvalue())
        z.writestr("index.html", index_html)
        z.writestr(f"{uuid}/info.xml", info_xml)
        z.writestr(f"{uuid}/metadata/metadata.xml", eml)
        for name, content in files.items():
            if name.startswith(f"{uuid}/public/") or name.startswith(f"{uuid}/private/"):
                z.writestr(name, content)
    hashes = [(name.split(f"{uuid}/", 1)[1], hashlib.sha256(content).hexdigest())
              for name, content in files.items()
              if name.startswith(f"{uuid}/public/") or name.startswith(f"{uuid}/private/")]
    report = [f"# {inventory['title']}", "", f"Source UUID: `{uuid}`", f"Source: `source-exports/{uuid}.zip` (extracted beside the ZIP)",
              f"Output: `{out.name}`", "", "## Preservation", "",
              "- Kept the source UUID, exact title and abstract text, ordered keywords, source parties and roles, geographic bounds, online links, categories, privileges, and attachment bytes.",
              f"- Source hierarchy: `{inventory['hierarchy']}`; status: `{inventory['status'] or 'not supplied'}`; metadata language: `{inventory['language'] or 'not supplied'}`.",
              "- Keywords, in source order: " + ("; ".join(f"`{item}`" for item in inventory["keywords"]) or "none") + ".",
              f"- Geographic extent: `{inventory['geographic_description']}`; bounds `{inventory['bounds']}`.",
              f"- Browse images, in source order: {', '.join(f'`{item}`' for item in inventory['browse']) or 'none'}.",
              f"- Online resources: {', '.join(f'`{name}` ({url})' for name, url in inventory['links']) or 'none'}.",
              f"- ISO distribution formats: {', '.join(inventory['formats']) or 'none'}.",
              f"- Non-publication citation dates: {', '.join(f'{kind} {date}' for kind, date in inventory['citation_dates']) or 'none supplied'}. No publication date was inferred.",
              "- Source catalogue IDs and usage counters were removed from `info.xml`; the MEF root indexes were regenerated."]
    report.append("- Responsible parties: " + "; ".join(
        f"{party['name'] or party['organization'] or party['email']} ({party['role'] or 'role missing'}; "
        f"{party['organization'] or 'no organization'}; {party['email'] or 'no email'})"
        for party in inventory["parties"]) + ".")
    if uuid in CORRECTED_PARTY_NAMES:
        report.append("- Corrected two mojibake author names in the EML output to Andrej Seliškar and Tomaž Seliškar, confirmed by the BIJH-hosted FloVegSi paper and ZRC/Cobiss researcher records: https://bijh.zrc-sazu.si/BISER/FloVegSi/Flo/FloVegSi.pdf and https://cris.cobiss.net/ecris/si/sl/researcher/5990. The source ISO export remains unchanged.")
    if uuid == "ce4ccbc2-ebba-43d7-af35-8aee7e6f7935":
        report.append("- Split the source's Related publications heading and citations into EML paragraphs at its explicit line-break boundaries; all wording is preserved.")
    if inventory["creator_role_unconfirmed"]:
        report.append("- The EML profile requires a creator, but the source does not assign that role. Following the data owner's instruction, the named source custodian or owner is mapped to Creator; the original source role is retained as an associated party. This role uncertainty is documented here, not in user-facing Additional information.")
    if not inventory["abstract"]:
        report.append("- The source has no abstract. The mandatory EML abstract explicitly records that absence; no resource description was invented.")
    if inventory["hierarchy"] == "Research sites":
        report.append("- This is a research-site record. The EML record retains that scope and does not claim a data download.")
    if uuid in REVIEW_NOTES:
        report.append("- Review needed: " + REVIEW_NOTES[uuid])
    report += ["", "## Attachment hashes", "", "| Source attachment | SHA-256 |", "| --- | --- |"]
    report += [f"| `{name}` | `{digest}` |" for name, digest in hashes]
    if not hashes:
        report.append("No source attachments.")
    report += ["", "## Verification", "", "The conversion test suite checks source/MEF identity, exact abstract and keywords, manifests, and attachment hashes. The generated XML is validated against the local EML-GBIF schema. Live catalogue import, indexing and rendering have not been performed.", ""]
    (ROOT / f"{slug}-preservation.md").write_text("\n".join(report), encoding="utf-8")
    return out


if __name__ == "__main__":
    for record_uuid, record_slug in RECORDS.items():
        print(package(record_uuid, record_slug))
