# Slovenian Bird Ringing Center Database (BRDbase)

Source UUID: `2a1a1d63-9b2d-48d2-931d-b18945a580d5`
Source: `source-exports/2a1a1d63-9b2d-48d2-931d-b18945a580d5.zip` (extracted beside the ZIP)
Output: `slovenian-bird-ringing-database-eml-gbif.mef`

## Preservation

- Kept the source UUID, exact title and abstract text, ordered keywords, source parties and roles, geographic bounds, online links, categories, privileges, and attachment bytes.
- Source hierarchy: `Services and databases`; status: `onGoing`; metadata language: `eng`.
- Keywords, in source order: `Research`; `Birdringing`; `RI-SI-LifeWatch`; `LifeWatch Slovenia`; `EURING`; `Slovenian Bird Ringing Center`; `Slovenian Museum of Natural History`.
- Geographic extent: `Slovenia`; bounds `{'westBoundLongitude': '13.365', 'eastBoundLongitude': '16.515', 'northBoundLatitude': '46.864', 'southBoundLatitude': '45.424'}`.
- Browse images, in source order: `Obrockovalska-baza_vnos-podatkov-2-768x796.jpg`, `PZ-SCOP_naslovnica.jpg`.
- Online resources: none.
- ISO distribution formats: none.
- Non-publication citation dates: none supplied. No publication date was inferred.
- Source catalogue IDs and usage counters were removed from `info.xml`; the MEF root indexes were regenerated.
- Responsible parties: Tomi Trilar (custodian; PMS; ttrilar@pms-lj.si); Tanja Pipan (pointOfContact; IZRK ZRC SAZU; pipan@zrc-sazu.si).
- The EML profile requires a creator, but the source does not assign that role. Following the data owner's instruction, the named source custodian or owner is mapped to Creator; the original source role is retained as an associated party. This role uncertainty is documented here, not in user-facing Additional information.

## Attachment hashes

| Source attachment | SHA-256 |
| --- | --- |
| `public/Obrockovalska-baza_vnos-podatkov-2-768x796.jpg` | `03456395c57aea9792286e9d1d95dc3900cdf2b7883e9bcf7a9fd8f72cbcc286` |
| `public/PZ-SCOP_naslovnica.jpg` | `4ce66214def2a6180c4dc04009ad7a07152900541f7830aa8fd2b3dc77f7fc98` |

## Verification

The conversion test suite checks source/MEF identity, exact abstract and keywords, manifests, and attachment hashes. The generated XML is validated against the local EML-GBIF schema. Local import and record display are documented in `README.md`; hosted deployment remains to be checked.
