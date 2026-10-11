# Marine phytoplankton database migration

Source UUID: `1f7b7000-1cc3-428f-974d-a688398f51e0`  
Source: `/Users/vids/Downloads/1f7b7000-1cc3-428f-974d-a688398f51e0`  
Output: `marine-phytoplankton-database-eml-gbif.mef`

## Preserved and mapped

- Kept the source UUID as the MEF UUID, EML `packageId`, and `alternateIdentifier`. Preserved the catalogue creation date, categories `Karst DB` and `MBP-NIB`, and source privileges. Removed source-catalogue `localId`, `siteId`, and `siteName` from `info.xml`.
- Preserved the title `Marine phytoplankton database`, metadata language `eng`, and all three keywords in source order: `LifeWatch Slovenia`, `Marine ecosystem`, and `Phytoplankton`.
- The ISO record names Andreja Ramšak (`andreja.ramsak@nib.si`) and Marine Biology Station Piran - National Institute of Biology as custodian. The EML profile requires a creator and contact, so the institution is used as creator and Andreja as contact; the source custodian role is retained as an associated party. The role caveats are documented here for migration provenance and are not included in the public EML record.
- Preserved the geographic description `Piran` and bounds west 13.2885, east 13.9793, north 45.6756, south 45.4259. Preserved ISO hierarchy level `Services and databases` in GBIF metadata and `additionalInfo`.
- The source abstract is empty, while the customized EML-GBIF profile requires one. The EML abstract says `No abstract was provided in the source ISO metadata.` This is an explicit notice of the source omission, not a generated description of the resource. The EML `additionalInfo` element is omitted.
- No citation date value, online resource, taxonomy, browse image, or public/private attachment is present in the source export. No publication date, download link, taxon, or image was added. The source has a citation date element typed `creation`, but its date value is empty.

## Validation and remaining limits

- EML-GBIF XSD validation passed with `xmllint --nonet --noout --schema schemas/eml-gbif/src/main/plugin/eml-gbif/schema/eml.xsd`.
- The three migration-specific tests passed. The repository EML-GBIF Python suite passed all 22 tests.
- The index transform emitted all three exact keywords in `tag` and `allKeywords`, with `tagNumber` 3.
- The original ISO export fails strict `gmd.xsd` validation: `identificationInfo` appears before required top-level hierarchy/contact elements, and the source `dateStamp` is empty. The original source was not changed.
- There are no source attachment bytes to compare or carry into the MEF. No local live catalogue import or rendered-record check was performed; hosted import, search, and display remain unverified.
