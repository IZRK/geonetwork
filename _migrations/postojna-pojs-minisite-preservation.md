# Postojnska jama (Postojna Cave) - bio-geo-chemo data (PO.J.S minisite)

Source UUID: `ce4ccbc2-ebba-43d7-af35-8aee7e6f7935`
Source: `source-exports/ce4ccbc2-ebba-43d7-af35-8aee7e6f7935.zip` (extracted beside the ZIP)
Output: `postojna-pojs-minisite-eml-gbif.mef`

## Preservation

- Kept the source UUID, exact title and abstract text, ordered keywords, source parties and roles, geographic bounds, online links, categories, privileges, and attachment bytes.
- Source hierarchy: `Research sites`; status: `onGoing`; metadata language: `eng`.
- Keywords, in source order: `RI-SI-LifeWatch`; `LifeWatch Slovenia`; `Cave fauna`; `Environmental parameters`; `Postojna Cave`; `LTER Slovenia`.
- Geographic extent: `Postojna`; bounds `{'westBoundLongitude': '14.2005', 'eastBoundLongitude': '14.2098', 'northBoundLatitude': '45.7841', 'southBoundLatitude': '45.7802'}`.
- Browse images, in source order: `IMG_20180404_103345402.jpg`.
- Online resources: none.
- ISO distribution formats: none.
- Non-publication citation dates: creation 2009-12-04. No publication date was inferred.
- Source catalogue IDs and usage counters were removed from `info.xml`; the MEF root indexes were regenerated.
- Responsible parties: magdalena.aljancic@zrc-sazu.si (role missing; no organization; magdalena.aljancic@zrc-sazu.si); Tanja Pipan (owner; IZRK ZRC SAZU; tanja.pipan@zrc-sazu.si).
- Split the source's Related publications heading and citations into EML paragraphs at its explicit line-break boundaries; all wording is preserved.
- The EML profile requires a creator, but the source does not assign that role. Following the data owner's instruction, the named source custodian or owner is mapped to Creator; the original source role is retained as an associated party. This role uncertainty is documented here, not in user-facing Additional information.
- This is a research-site record. The EML record retains that scope and does not claim a data download.
- Review needed: Conditional candidate: research-site metadata and no data link; confirm GBIF publication scope with the owner.

## Attachment hashes

| Source attachment | SHA-256 |
| --- | --- |
| `public/IMG_20180404_103345402.jpg` | `63ef5a6f4c6c192d5967cd6a04880776e2640a239b61bcf35e16754b458e63f7` |

## Verification

The conversion test suite checks source/MEF identity, exact abstract and keywords, manifests, and attachment hashes. The generated XML is validated against the local EML-GBIF schema. Local import and record display are documented in `README.md`; hosted deployment remains to be checked.
