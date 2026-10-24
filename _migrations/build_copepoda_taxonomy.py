"""Embed source-workbook order relationships in the Copepoda EML MEF."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree as ET
from zipfile import ZipFile


UUID = "c7710542-10ea-43e8-b4d7-9bdd3d559905"
DEFAULT_MEF = Path(__file__).with_name("copepoda-eml-gbif-preserved.mef")
DEFAULT_TAXONOMY = Path(__file__).with_name("copepoda-taxonomy.csv")
METADATA = f"{UUID}/metadata/metadata.xml"


def embed_taxonomy(metadata: bytes, taxonomy: Path) -> bytes:
    root = ET.fromstring(metadata)
    if root.get("packageId") != UUID:
        raise ValueError("Unexpected record UUID")
    coverage = root.find("./dataset/coverage/taxonomicCoverage")
    if coverage is None:
        raise ValueError("Missing taxonomic coverage")

    classifications = coverage.findall("taxonomicClassification")
    orders = {node.findtext("taxonRankValue"): node for node in classifications
              if node.findtext("taxonRankName") == "Order"}
    species_nodes = coverage.findall(".//taxonomicClassification")
    species = {node.findtext("taxonRankValue"): node for node in species_nodes
               if node.findtext("taxonRankName") == "Species"}
    if set(orders) != {"Cyclopoida", "Harpacticoida"} or len(species) != 30:
        raise ValueError("Unexpected source classifications")

    with taxonomy.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["species", "order"]:
            raise ValueError("Unexpected taxonomy columns")
        rows = list(reader)
    if len(rows) != len(species) or {row["species"] for row in rows} != set(species):
        raise ValueError("Taxonomy species do not match the MEF")
    if any(row["order"] not in orders for row in rows):
        raise ValueError("Unknown order in taxonomy")

    parents = {child: parent for parent in coverage.iter()
               for child in parent if child.tag == "taxonomicClassification"}
    for node in species.values():
        parents[node].remove(node)
    for row in rows:
        orders[row["order"]].append(species[row["species"]])
    ET.register_namespace("eml", "https://eml.ecoinformatics.org/eml-2.2.0")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build(source: Path, output: Path, taxonomy: Path = DEFAULT_TAXONOMY) -> None:
    with NamedTemporaryFile(dir=output.parent, suffix=".mef", delete=False) as temp:
        temporary = Path(temp.name)
    try:
        with ZipFile(source) as archive:
            if METADATA not in archive.namelist():
                raise ValueError("MEF metadata is missing")
            updated = embed_taxonomy(archive.read(METADATA), taxonomy)
            with ZipFile(temporary, "w") as destination:
                for member in archive.infolist():
                    destination.writestr(member, updated if member.filename == METADATA
                                         else archive.read(member.filename))
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?", default=DEFAULT_MEF)
    parser.add_argument("output", type=Path, nargs="?", default=DEFAULT_MEF)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    args = parser.parse_args()
    build(args.source, args.output, args.taxonomy)
