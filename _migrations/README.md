# EML migration packages

The eight MEFs in this directory are the import packages for the `izrk` merge.
The original exports are not committed. On 24 October 2026, each archive was
opened and validated against the local EML-GBIF XSD. The source exports in
`~/Downloads/<uuid>/<uuid>/` were compared with the packages: record identity,
title, abstract, keywords, geographic coordinates, source links, categories,
privileges, attachment manifests, and attachment SHA-256 hashes. The EML index
transform returned every keyword in `tag` and `allKeywords` with the correct
`tagNumber`; browse image counts matched the source records. Pollen was already
EML-GBIF in its source export; its taxonomy relationships were added to the
MEF. Branch-specific build scripts and tests have been removed after this
audit; the pre-existing shared taxonomy test remains.

| Package | Source UUID | Keywords | Public files | Browse images |
| --- | --- | ---: | ---: | ---: |
| `amphipoda-eml-gbif.mef` | `f39e56c2-65d4-43d2-b5f2-e707229777bf` | 6 | 5 | 2 |
| `copepoda-eml-gbif-preserved.mef` | `c7710542-10ea-43e8-b4d7-9bdd3d559905` | 10 | 2 | 1 |
| `karst-microbiological-database-eml-gbif-preserved.mef` | `28b6a390-8254-479b-ba55-c70f59e121d6` | 9 | 1 | 1 |
| `marine-phytoplankton-database-eml-gbif.mef` | `1f7b7000-1cc3-428f-974d-a688398f51e0` | 3 | 0 | 0 |
| `pollen-eml-gbif.mef` | `9f64b6e3-22be-4f17-9cc0-8658c7817867` | 4 | 0 | 0 |
| `postojna-minisites-eml-gbif-preserved.mef` | `8306e789-a3e5-40b2-aad4-aa69436a063c` | 6 | 1 | 1 |
| `postojna-planina-lter-eml-gbif.mef` | `d3011b1e-3aa5-4b61-a3bc-94da67f582c8` | 6 | 3 | 3 |
| `vegetation-slovenia-eml-gbif.mef` | `89ce7bbf-cf1b-4fe8-9ef9-70c817bc3789` | 7 | 4 | 2 |

The marine phytoplankton source has no abstract, so its required EML abstract
explicitly says so. Some source records do not identify a creator or
publication date; the individual preservation reports explain the chosen
role and date mappings. The Copepoda package's root indexes and source
attachment dates were corrected during this audit.

Before importing, deploy this branch's EML-GBIF schema, formatter, and index
changes to the target catalogue. Import each MEF with the intended UUID
replacement handling. Reindex existing EML records after deploying the index
stylesheet, then check record display, images, and keyword links in the live
catalogue. These live checks have not been performed by the repository audit.

The taxonomy relationships in `copepoda-eml-gbif-preserved.mef` and
`pollen-eml-gbif.mef` are embedded in their metadata. The two small taxonomy
CSV files retain the source relationships and GBIF references used to create
those packages; neither is required for import. A fresh migration from a new
source export requires a new, reviewed conversion rather than rebuilding these
fixed packages in place.
