"""Nest source-verified pollen taxon relationships in an exported EML MEF."""

from __future__ import annotations

import argparse
import csv
import html
import io
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree as ET
from zipfile import ZipFile


UUID = "9f64b6e3-22be-4f17-9cc0-8658c7817867"
METADATA = f"{UUID}/metadata/metadata.xml"
RELATION_COLUMNS = ["child_rank", "child_name", "parent_rank", "parent_name", "source_reference"]


def taxon_key(node: ET.Element) -> tuple[str, str]:
    return (node.findtext("taxonRankName", "").strip().lower(),
            node.findtext("taxonRankValue", "").strip())


def embed_taxonomy(metadata: bytes, relationships: Path) -> bytes:
    root = ET.fromstring(metadata)
    package_id = root.get("packageId", "")
    if package_id.rstrip("/").rsplit("/", 1)[-1] != UUID:
        raise ValueError("Unexpected pollen record UUID")
    root.set("packageId", UUID)

    with relationships.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != RELATION_COLUMNS:
            raise ValueError("Unexpected relationship columns")
        rows = list(reader)
    if not rows or any(not all(row.get(column, "").strip() for column in RELATION_COLUMNS)
                       for row in rows):
        raise ValueError("Every relationship needs two taxa and a source reference")

    coverages = root.findall("./dataset/coverage/taxonomicCoverage")
    if not coverages:
        raise ValueError("Pollen record has no taxonomic coverage")

    parents = {child: parent for coverage in coverages for parent in coverage.iter()
               for child in parent if child.tag == "taxonomicClassification"}
    nodes = [node for coverage in coverages
             for node in coverage.iter("taxonomicClassification")]
    by_key = {}
    for node in nodes:
        by_key.setdefault(taxon_key(node), []).append(node)

    def resolve_or_add(key: tuple[str, str]) -> ET.Element:
        matches = by_key.get(key, [])
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(f"Relationship taxon is ambiguous: {key}")
        if len(coverages) != 1:
            raise ValueError(f"Cannot add missing taxon across multiple coverages: {key}")
        node = ET.Element("taxonomicClassification")
        ET.SubElement(node, "taxonRankName").text = key[0].title()
        ET.SubElement(node, "taxonRankValue").text = key[1]
        coverages[0].append(node)
        parents[node] = coverages[0]
        by_key[key] = [node]
        return node

    moved = set()
    for row in rows:
        child_key = (row["child_rank"].strip().lower(), row["child_name"].strip())
        parent_key = (row["parent_rank"].strip().lower(), row["parent_name"].strip())
        child = resolve_or_add(child_key)
        parent = resolve_or_add(parent_key)
        if child is parent:
            raise ValueError(f"A taxon cannot be its own parent: {child_key}")
        if child in moved or parents[child] not in coverages:
            raise ValueError(f"Taxon has more than one parent or is already nested: {child_key}")
        ancestor = parent
        while ancestor in parents:
            if ancestor is child:
                raise ValueError(f"Taxonomy cycle at {child_key}")
            ancestor = parents[ancestor]
        if ancestor is not parents[child]:
            raise ValueError(f"Taxa are in different taxonomic coverages: {child_key}")
        parents[child].remove(child)
        parent.append(child)
        parents[child] = parent
        moved.add(child)

    ET.register_namespace("eml", "https://eml.ecoinformatics.org/eml-2.2.0")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _check_info(info: bytes) -> None:
    root = ET.fromstring(info)
    if root.findtext("./general/uuid") != UUID:
        raise ValueError("Unexpected pollen record UUID in MEF info.xml")


def _normalize_info(info: bytes) -> bytes:
    root = ET.fromstring(info)
    general = root.find("./general")
    if general is None:
        raise ValueError("Pollen MEF info.xml has no general section")
    changed = False
    schema = general.find("schema")
    if schema is not None and schema.text != "eml-gbif":
        schema.text = "eml-gbif"
        changed = True
    change_date = general.find("changeDate")
    if change_date is not None:
        change_date.text = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z")
        changed = True
    for name in ("localId", "siteId", "siteName", "rating", "popularity"):
        element = general.find(name)
        if element is not None:
            general.remove(element)
            changed = True
    if not changed:
        return info
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _index_csv(data: bytes, metadata: bytes) -> bytes:
    rows = list(csv.DictReader(data.decode("utf-8-sig").splitlines(), delimiter=";"))
    if len(rows) != 1:
        raise ValueError("Pollen MEF index.csv must contain exactly one record row")
    root = ET.fromstring(metadata)
    row = rows[0]
    row.update({
        "schema": "eml-gbif",
        "uuid": UUID,
        "id": "",
        "title": root.findtext("./dataset/title", ""),
        "abstract": " ".join(
            " ".join((paragraph.text or "").split())
            for paragraph in root.findall("./dataset/abstract/para")
        ),
    })
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(row), delimiter=";",
                            quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _index_html(metadata: bytes) -> bytes:
    root = ET.fromstring(metadata)
    title = html.escape(root.findtext("./dataset/title", ""))
    abstract = html.escape(" ".join(
        " ".join((paragraph.text or "").split())
        for paragraph in root.findall("./dataset/abstract/para")
    ))
    content = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        f"<title>{title}</title><h1>{title}</h1><p>{abstract}</p>"
        f"<p>UUID: {UUID}</p></html>\n"
    )
    return content.encode("utf-8")


def build(source: Path, output: Path, relationships: Path) -> None:
    with NamedTemporaryFile(dir=output.parent, suffix=".mef", delete=False) as temporary_file:
        temporary = Path(temporary_file.name)
    try:
        if source.is_dir():
            record_dir = source / UUID
            info_path = record_dir / "info.xml"
            metadata_path = record_dir / "metadata" / "metadata.xml"
            if not info_path.is_file() or not metadata_path.is_file():
                raise ValueError("Pollen MEF directory needs info.xml and metadata/metadata.xml")
            _check_info(info_path.read_bytes())
            updated = embed_taxonomy(metadata_path.read_bytes(), relationships)
            updated_info = _normalize_info(info_path.read_bytes())
            with ZipFile(temporary, "w") as destination:
                for path in sorted(source.rglob("*")):
                    if path.is_file():
                        name = path.relative_to(source).as_posix()
                        content = path.read_bytes()
                        if path == metadata_path:
                            content = updated
                        elif path == info_path:
                            content = updated_info
                        elif name == "index.csv":
                            content = _index_csv(content, updated)
                        elif name == "index.html":
                            content = _index_html(updated)
                        destination.writestr(name, content)
        else:
            with ZipFile(source) as archive:
                names = archive.namelist()
                info_name = f"{UUID}/info.xml"
                if info_name not in names or METADATA not in names:
                    raise ValueError("Pollen MEF info.xml or metadata is missing")
                _check_info(archive.read(info_name))
                updated = embed_taxonomy(archive.read(METADATA), relationships)
                updated_info = _normalize_info(archive.read(info_name))
                with ZipFile(temporary, "w") as destination:
                    destination.comment = archive.comment
                    for member in archive.infolist():
                        content = archive.read(member.filename)
                        if member.filename == METADATA:
                            content = updated
                        elif member.filename == info_name:
                            content = updated_info
                        elif member.filename == "index.csv":
                            content = _index_csv(content, updated)
                        elif member.filename == "index.html":
                            content = _index_html(updated)
                        destination.writestr(member, content)
        temporary.chmod(0o644)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="current exported pollen MEF")
    parser.add_argument("output", type=Path, help="updated import-ready MEF")
    parser.add_argument("--relationships", required=True, type=Path,
                        help="CSV with recorded taxon parent links and source references")
    args = parser.parse_args()
    build(args.source, args.output, args.relationships)
