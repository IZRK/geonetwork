# Open problems

## Source records need owner review before GBIF publication

- Marine genomic ARMS (`b5c2c64a-325b-42d1-b5ad-2198ad434a55`) has no
  abstract or data access link. Confirm its scope, description, and access.
- Škocjan airborne bacteria (`6006d62c-5143-4bbc-ad4c-9d9375b0f499`) and
  detected pathogens (`1b83ee14-6498-4f9b-a297-eb1692095c1a`) describe Excel
  data, but their exports include only images and no data link. Obtain the data
  before presenting these records as accessible datasets.
- Predjama PR-2 (`cec7e833-ef3c-443d-984b-5e0b15418375`) has no abstract and
  misspells “System” in its title. Correct the source with the owner.
- The Postojna PO.J.S, Predjama PR-2, and Škocjan Caves LTER records describe
  research sites. Confirm whether each belongs in GBIF before publishing.

The MEFs preserve these omissions and do not invent descriptions or data links.
They were imported into a local GeoNetwork catalogue on 25 October 2026 with
the Publish option off; that import was not GBIF publication.

## Source ISO metadata remains incomplete

The original ISO exports for Copepoda, Karst microbiology, Amphipoda,
Vegetation of Slovenia, Postojna minisites, Marine phytoplankton, and Škocjan
detected pathogens fail the repository's strict ISO 19139 schema, usually
because required top-level contact or `dateStamp` fields are absent. The
Marine phytoplankton record also has no abstract. Their converted EML packages
validate against the local EML-GBIF profile, but the original ISO records
should be corrected if they remain in use. Do not infer missing publication
dates from unrelated citation or catalogue dates.

The FloVegSi ISO record (`9a5a0578-f6c5-4c44-9ca6-e23baada5ffb`) contains
two corrupted author names. The EML package corrects them to Andrej Seliškar
and Tomaž Seliškar; the source record still needs correction.

## Copepoda description overstates the data

The source calls the workbook “species abundance,” but its species-by-cave
cells record presence marks, not numeric abundance. Ask the data owner to
update the description if it refers to this workbook. The migration package
preserves the source description and does not add inferred absences.

## Portal artwork is missing from source

The portal templates reference project logos under
`catalog/views/default/images/izrk/projects/` and a footer logo at
`catalog/views/default/images/izrk/footer-logo.png`. The source folder has only
`favicon.png` and `logo.png`. Supply the actual institutional artwork before
those references can render after deployment.

## Shared extent coordinates resemble editable fields

The shared extent formatter renders coordinates as read-only HTML inputs.
They can look editable on record pages and in PDF output. The separate PDF
fix should handle this shared renderer without coupling it to the EML
migration branch.

## Local development environment

- Java 25 introduces `java.lang.IO`, which conflicts with the project's
  `org.fao.geonet.utils.IO` imports in `KeywordsApi` and `DownloadArchive`.
  Build this Java 11 project with a supported JDK; services compiled with
  JDK 17 locally.
- Local Jetty regenerated the missing
  `web/src/main/webapp/WEB-INF/data/config/encryptor.properties` key after a
  restart. Persist that key outside generated webapp content before relying on
  locally encrypted catalogue credentials.
