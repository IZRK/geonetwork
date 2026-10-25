# FloVegSi Database (Fauna, Flora and Vegetation of Slovenia) BIJH ZRC SAZU

Source UUID: `9a5a0578-f6c5-4c44-9ca6-e23baada5ffb`
Source: `source-exports/9a5a0578-f6c5-4c44-9ca6-e23baada5ffb.zip` (extracted beside the ZIP)
Output: `flovegsi-database-eml-gbif.mef`

## Preservation

- Kept the source UUID, exact title and abstract text, ordered keywords, source parties and roles, geographic bounds, online links, categories, privileges, and attachment bytes.
- Source hierarchy: `Services and databases`; status: `onGoing`; metadata language: `eng`.
- Keywords, in source order: `Flora`; `Vegetation`; `Fauna`; `FloVegSi`; `BIJH`; `LifeWatch Slovenia`; `ZRC SAZU`; `RI-SI-LifeWatch`.
- Geographic extent: `Slovenia`; bounds `{'westBoundLongitude': '13.3753', 'eastBoundLongitude': '16.6106', 'northBoundLatitude': '46.8766', 'southBoundLatitude': '45.4218'}`.
- Browse images, in source order: `FlovegSi naslovnica_0.jpg`.
- Online resources: none.
- ISO distribution formats: none.
- Non-publication citation dates: none supplied. No publication date was inferred.
- Source catalogue IDs and usage counters were removed from `info.xml`; the MEF root indexes were regenerated.
- Responsible parties: IZRK (pointOfContact; IZRK; no email); Brane Vreš (custodian; BIJH ZRC SAZU; branevr@zrc-sazu.si); Andrej Seliškar (author; BIJH ZRC SAZU; no email); Tomaž Seliškar (author; BIJH ZRC SAZU; no email).
- Corrected two mojibake author names in the EML output to Andrej Seliškar and Tomaž Seliškar, confirmed by the BIJH-hosted FloVegSi paper and ZRC/Cobiss researcher records: https://bijh.zrc-sazu.si/BISER/FloVegSi/Flo/FloVegSi.pdf and https://cris.cobiss.net/ecris/si/sl/researcher/5990. The source ISO export remains unchanged.

## Attachment hashes

| Source attachment | SHA-256 |
| --- | --- |
| `public/FlovegSi naslovnica_0.jpg` | `8aae8ef6f572aa5b3a95e440c6247a61beca1e8ff89d5abb2fffdb781d236ae0` |

## Verification

The conversion test suite checks source/MEF identity, exact abstract and keywords, manifests, and attachment hashes. The generated XML is validated against the local EML-GBIF schema. Local import and record display are documented in `README.md`; hosted deployment remains to be checked.
