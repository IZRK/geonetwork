# Vegetation of Slovenia database migration

Source UUID: `89ce7bbf-cf1b-4fe8-9ef9-70c817bc3789`
Source: supplied extracted ISO MEF record directory (source not committed)
Output: `vegetation-slovenia-eml-gbif.mef`

## Preserved and mapped

- Kept the source UUID as the EML `packageId`, alternate identifier, and MEF UUID. Preserved the source catalogue creation date, categories, privileges, and all four public attachments; removed source-instance IDs from `info.xml`.
- Preserved the title, full abstract (two source paragraphs), and all seven keywords in source order: Flora; Vegetation; TurboVeg; BIJH; LifeWatch Slovenia; ZRC SAZU; RI-SI-LifeWatch.
- Mapped the source organization `BIJH ZRC SAZU` to the profile-required creator. The two named parties remain associated custodians: Urban Šilc (`urban.silc@zrc-sazu.si`) and Filip Küzmič (`filip.kuzmic@zrc-sazu.si`). Filip is also used as the required EML contact; the source gives him a custodian role, so the contact role is not confirmed. The role caveats are recorded here rather than in user-facing `additionalInfo`.
- Preserved the geographic extent as Slovenia, with bounds west 13.3753, east 16.6106, north 46.8766, south 45.4218. Mapped the source hierarchy `Services and databases`, status `onGoing`, and metadata language `eng` to `additionalInfo`; hierarchy is also in GBIF metadata.
- Preserved both original download URLs in separate EML distribution entries with readable descriptions. The source ISO citation date is `2003-01-01` with type `creation`, so it remains identified as a creation date and is not used as `pubDate`.
- Preserved the two browse images in source order. The first image is the GBIF resource logo and the second is referenced through the local additional-overview convention.

## Attachments

All output attachment hashes match the supplied source bytes (SHA-256):

| Public attachment | SHA-256 |
| --- | --- |
| `Slovenian_URN NBN SI doc-YJI65ZCZ.pdf` | `7cf021fd0ebb16746c2fbcc20deb8528a00a73656f9ec0203732435b79acd5d4` |
| `VegSlo_UŠ.JPG` | `0956ad60198853c8d1af75a5cf335b6f60a1da3f4b749ff1fb2317bbdcf000ff` |
| `VegSlo_UŠ2.JPG` | `03dc284d012ff6ac97db97f1103945cf352c6d6a11ec5f6e344b91933fbe6e4f` |
| `Vegetation database 2012.pdf` | `75d2081ed6e387f5baecd0dbaa0296443b11c9bf918809287330f7d58fbf0df5` |

The extracted source image filenames use decomposed Unicode while the source manifest uses composed Unicode. The MEF uses the manifest's composed filenames and contains the same attachment bytes, keeping its manifest and packaged paths consistent.

## Validation and remaining limits

- EML-GBIF schema validation passed with `xmllint --nonet --noout --schema schemas/eml-gbif/src/main/plugin/eml-gbif/schema/eml.xsd`.
- Direct source comparison confirmed content, access settings, and attachment bytes.
- The record's index transform emitted all seven exact keywords in both `tag` and `allKeywords`, with `tagNumber` 7.
- The source ISO XML fails strict `gmd.xsd` validation: it is missing required top-level metadata contact and `dateStamp` fields before `identificationInfo`. The source was not modified; this migration records their absence. The source also has no taxonomy or temporal extent, so none were added.
- Local import and record display are documented in `README.md`; hosted search and display remain to be checked. Importing this MEF does not deploy formatter code or reindex records in a hosted catalogue.


- EML Creator mapping: following the data owner's instruction, used Urban Šilc (custodian; BIJH ZRC SAZU), Filip Küzmič (custodian; BIJH ZRC SAZU) as the required EML Creator(s); the ISO source role remains represented as an associated party.
