# EML migration packages

This directory contains 17 MEFs for the `izrk` merge. Eight packages already
existed; nine more were converted from the reviewed ISO 19139 records on
24 October 2026. All 17 source ZIPs and their extracted contents are in
`source-exports/` locally and ignored by Git. They remain available for audit;
the original exports were not modified. Pollen was already EML-GBIF in its
source export. The committed MEFs are the import artifacts. The one-off
converter was removed because its private source exports are not in this
repository; a new migration requires a new reviewed conversion.

All nine new MEFs passed the local EML-GBIF XSD and independent comparison of
record identity, title, abstract, keywords, geographic coordinates, source
links, categories, privileges, attachment manifests, and attachment SHA-256
hashes. The EML index transform returned every keyword in `tag` and
`allKeywords` with the correct `tagNumber`. The six existing taxonomy tests also
passed. Per-record preservation reports are beside the packages.

| Package | Source UUID | Keywords | Public files | Browse images |
| --- | --- | ---: | ---: | ---: |
| `amphipoda-eml-gbif.mef` | `f39e56c2-65d4-43d2-b5f2-e707229777bf` | 6 | 5 | 2 |
| `copepoda-eml-gbif-preserved.mef` | `c7710542-10ea-43e8-b4d7-9bdd3d559905` | 10 | 2 | 1 |
| `flovegsi-database-eml-gbif.mef` | `9a5a0578-f6c5-4c44-9ca6-e23baada5ffb` | 8 | 1 | 1 |
| `institute-of-biology-herbarium-eml-gbif.mef` | `293dcc3b-8e9d-4c74-bfb2-67eddee69417` | 9 | 2 | 1 |
| `karst-microbiological-database-eml-gbif-preserved.mef` | `28b6a390-8254-479b-ba55-c70f59e121d6` | 9 | 1 | 1 |
| `marine-genomic-arms-database-eml-gbif.mef` | `b5c2c64a-325b-42d1-b5ad-2198ad434a55` | 3 | 0 | 0 |
| `marine-phytoplankton-database-eml-gbif.mef` | `1f7b7000-1cc3-428f-974d-a688398f51e0` | 3 | 0 | 0 |
| `pollen-eml-gbif.mef` | `9f64b6e3-22be-4f17-9cc0-8658c7817867` | 4 | 0 | 0 |
| `postojna-minisites-eml-gbif-preserved.mef` | `8306e789-a3e5-40b2-aad4-aa69436a063c` | 6 | 1 | 1 |
| `postojna-planina-lter-eml-gbif.mef` | `d3011b1e-3aa5-4b61-a3bc-94da67f582c8` | 6 | 3 | 3 |
| `postojna-pojs-minisite-eml-gbif.mef` | `ce4ccbc2-ebba-43d7-af35-8aee7e6f7935` | 6 | 1 | 1 |
| `predjama-pr2-minisite-eml-gbif.mef` | `cec7e833-ef3c-443d-984b-5e0b15418375` | 6 | 1 | 1 |
| `skocjan-airborne-bacteria-eml-gbif.mef` | `6006d62c-5143-4bbc-ad4c-9d9375b0f499` | 7 | 2 | 1 |
| `skocjan-caves-lter-site-eml-gbif.mef` | `aff1a1d3-46df-46df-a693-7d249134633c` | 7 | 2 | 2 |
| `skocjan-detected-pathogens-eml-gbif.mef` | `1b83ee14-6498-4f9b-a297-eb1692095c1a` | 7 | 2 | 1 |
| `slovenian-bird-ringing-database-eml-gbif.mef` | `2a1a1d63-9b2d-48d2-931d-b18945a580d5` | 7 | 2 | 2 |
| `vegetation-slovenia-eml-gbif.mef` | `89ce7bbf-cf1b-4fe8-9ef9-70c817bc3789` | 7 | 4 | 2 |

The marine phytoplankton source has no abstract, so its required EML abstract
explicitly says so. Some source records do not identify a creator or
publication date; the individual preservation reports explain the chosen
role and date mappings. The Copepoda package's root indexes and source
attachment dates were corrected during this audit.

The four packages for marine genomic ARMS, Škocjan Caves LTER, Postojna PO.J.S,
and Predjama PR-2 represent conditional candidates. Their EML validates, but
their suitability for GBIF publication needs a data-owner decision. The ARMS
and Predjama source records have no abstract. The two Škocjan bacterial records
describe Excel data but include no data file or online data link. Those gaps
are recorded in `PROBLEMS.md`; no data or description was fabricated.

Before importing, deploy this branch's EML-GBIF schema, formatter, and index
changes to the target catalogue. Import each MEF with the intended UUID
replacement handling. Reindex existing EML records after deploying the index
stylesheet, then check record display, images, and keyword links in the live
catalogue. The local catalogue checks are recorded below; repeat them for any
other target catalogue.

The taxonomy relationships in `copepoda-eml-gbif-preserved.mef` and
`pollen-eml-gbif.mef` are embedded in their metadata. The two small taxonomy
CSV files retain the source relationships and GBIF references used to create
those packages; neither is required for import. A fresh migration from a new
source export requires a new, reviewed conversion rather than rebuilding these
fixed packages in place.

## Local catalogue import (25 October 2026)

The 17 MEFs in this table were imported through Firefox Developer Edition into
`http://localhost:8080/geonetwork`. The batch import report listed 17 successful
MEF imports (local IDs 123–139) and no errors. Existing same-UUID records were
deleted and replaced so their schema changed to EML-GBIF; the MEF packages
supplied the replacement privileges and attachments. The original UUIDs were
retained. The import form's **Publish** option remained off; this operation did
not publish to GBIF.

Before replacement, the local H2 database and GeoNetwork data directory were
saved at `source-exports/geonetwork-before-eml-import-20261024.tar.gz`. The
archive was integrity checked and remains outside Git with the source exports.
All 17 UUID pages were then opened in the local catalogue and displayed
**EML / GBIF** with their expected overview-image counts and keyword sections.
A Vegetation keyword filter returned the Vegetation of Slovenia record. Files
for the Herbarium and Amphipoda records matched their MEF attachments by
SHA-256. The package tests passed after import. Run them from the repository
root with `python3 -m unittest discover -s _migrations -p 'test_*.py'`.
Checks against the original ISO exports run when `source-exports/` is present;
committed-package checks run without it. XML validation requires `xmllint`,
and the index transform check requires a built web archive and JDK.
