# Problems and follow-up

## Spatial extent coordinates looked editable on record pages and PDF exports (resolved in source, 2026-10-24)

The shared extent renderer emitted coordinate values as `readonly` HTML inputs.
They could not be edited in the record page, but looked like form fields and
raised the risk of being represented as controls in PDF output. The renderer
now emits accessible text spans with the same values and labels, retaining the
extent image. A Saxon regression test verifies the rendered coordinates are
text and that no input elements are generated.

## Pollen MEF retained source-catalogue identifiers (resolved in MEF, 2026-10-18)

The pollen EML package used the source catalogue URL as `packageId` and kept
its `localId`, `siteId`, `siteName`, rating, and popularity in `info.xml` and
the root index files. That could make an import carry stale identity data into
another catalogue. The taxonomy builder now sets `packageId` to the MEF UUID,
removes those source-instance fields, and regenerates the root index files
without the source database ID. The package was rebuilt from the source export;
the updated identity and taxonomy tests pass.

## EML extents on zero longitude or latitude were omitted from the map index (resolved in source, 2026-10-18)

The EML-GBIF index used XPath numeric truthiness to decide whether all four
bounding coordinates were present. A valid zero longitude or latitude is
false in XPath, so extents touching the equator or prime meridian were omitted.
Its `##.00` format also rendered zero as `.00`. Indexing now checks numeric
castability and uses `0.00`; a regression test confirms zero coordinates and
the resulting `geoBox` are indexed. The committed EML migration packages all
produce valid `geoBox` values. Existing catalogue records need reindexing for
the source fix to affect their map extents.

## Legacy EML 2.1.1 records were skipped by the EML-GBIF index transform (resolved in source, 2026-10-18)

The bundled EML-GBIF sample MEFs still include EML 2.1.1 records, but the
index stylesheet selected only the EML 2.2.0 root element. The Tanzanian
sample's two valid geographic extents and keywords therefore produced no map
or search fields. The index transform now accepts both EML root namespaces;
a regression test runs the bundled sample through the real index transform
and checks its extents, title, and keywords.

## WebP search thumbnails failed for local attachments (resolved in source, 2026-10-17)

EML-GBIF indexes a local `resourceLogoUrl` as an attachment URL. Search cards
append `?size=140` to attachment URLs, so the server tries to resize the WebP
with Java `ImageIO`. The packaged dependency set has no WebP reader, causing
the thumbnail request to fail even though browsers can display the original.
ISO indexing preserves the source overview URL, so an external WebP URL avoids
the resize path; a local ISO WebP attachment would hit the same problem.
The search thumbnail filter now requests WebP attachments without `size` while
keeping resized requests for supported image formats. A JavaScript regression
test covers WebP, PNG, query strings, and external images. Deploy the updated
web UI for the change to take effect.

## Merge review: migration builders retained machine-specific defaults and compiled bytecode (resolved in source, 2026-10-17)

The branch tracked `_migrations/__pycache__/test_postojna_migration.cpython-313.pyc`,
which is generated for one Python version and is not source. The Marine,
Postojna-Planina, and Vegetation migration builders also defaulted `--source`
to `/Users/vids/Downloads/...`. The bytecode is removed and Python cache files
are ignored. Those builders now require a caller-supplied `--source` path, and
the migration README documents portable invocations. CLI regression tests
check that all three reject a missing source path.

## Pollen taxonomy relationships were missing from the record (resolved in MEF, 2026-10-17)

The formatter no longer loads record-specific taxonomy from the app. The
Copepoda record `c7710542-10ea-43e8-b4d7-9bdd3d559905` now has its two orders
and 30 species nested in its import-ready MEF, based on the source workbook.
Its rendered tree and EML schema validation pass. The pollen record
`9f64b6e3-22be-4f17-9cc0-8658c7817867` had two curated relationships in the
removed plugin file: `Valeriana` under `Caprifoliaceae`, and
`Valerianella eriocarpa` under `Caprifoliaceae` / `Valerianella`. The September
2026 MEF export contained `Valeriana` and `Valerianella eriocarpa` as flat
classifications, but not their GBIF family and genus parents. The formatter no
longer contains these record-specific links. `_migrations/pollen-eml-gbif.mef`
now carries the family and genus entries and the nested classifications, with
the GBIF source pages recorded in `_migrations/pollen-taxonomy.csv`. The MEF
passes local EML-GBIF schema validation, and the rendered taxonomy shows the
family, both genera, and species. The catalogue record still needs this MEF
imported during deployment.

## Merge review: image modal could turn a metadata URL into HTML (resolved in source, 2026-10-17)

`schemas/eml-gbif/.../xsl-view/view.xsl` accepts an HTTP(S)
`resourceLogoUrl` from imported EML as an overview image. On click,
`gnImgModal` in `web-ui/.../UtilityDirective.js` read that image URL and
interpolated it into an HTML string for both the modal ID and image `src`.
The fallback also used the clicked image when no indexed overview matched.
A quoted URL was safely escaped in the XSL output, but the DOM attribute
returned the decoded quote before `angular.element(markup)` reparsed it. A URL
containing `" onerror="...` could therefore create an event attribute in the
modal. The modal now parses only static markup, then assigns the ID and image
URL as attributes and the caption as text. Regression tests cover quoted URLs,
IDs, and captions; deploy the updated web UI for the fix to take effect.

## Merge review: blank-group handling is inconsistent (resolved in source, 2026-10-17)

`MetadataInsertDeleteApi.checkGroupIsWorkspace` accepted all blank strings,
including whitespace. Other paths in the same class used
`StringUtils.isNotEmpty(group)` before `Integer.parseInt(group)` (the WMC import
privilege path and validation path). Thus `group="   "` passed the check but
failed later, potentially after record creation. The duplicate endpoint also
declared `group` required while skipping validation for a blank value.
The four request paths now normalize and validate `group` at their boundaries.
Optional blank values become `null`, numeric IDs are canonicalized, and the
duplicate endpoint rejects blank values before looking up or creating a record.
All downstream import, validation, workflow and privilege calls receive the
normalized value. Six regression tests cover the helper and affected routes.

## Merge review: EML overview indexing requires an optional identifier (resolved in source, 2026-10-17)

`schemas/eml-gbif/.../index-fields/index.xsl` builds local attachment URLs
from `dataset/alternateIdentifier[1]` and returned no overview if it was absent.
EML already has a root `packageId`, and the formatter itself uses GeoNetwork's
record UUID. A valid record with `packageId` and a local `resourceLogoUrl`, but
no alternate identifier, indexed as `hasOverview=false`; a standalone transform
confirmed this result. The indexing service now passes the catalogue UUID to
the stylesheet. When used without that parameter, the stylesheet accepts a
UUID-shaped `packageId` as a fallback. Tests cover both paths, a different
`packageId`, unsafe image references, and an invalid fallback.

## Merge review: migration verification is not reproducible in a clean checkout (resolved in source, 2026-10-17)

The migration tests no longer read ISO exports from a developer's Downloads
directory. Optional source comparisons use explicit environment variables and
skip when the exports are absent; checks against committed MEFs still run.
Standalone index transforms now supply a test node URL without a live
GeoNetwork application context. The Linux QA workflow runs the full migration
suite after building GeoNetwork, with required Java and XML tools checked.
All 26 tests passed locally with the source exports supplied; the clean
checkout run passed with nine source comparisons skipped.

## Merge review: EML keyword links break on URL or JSON punctuation (resolved in source, 2026-10-17)

`schemas/eml-gbif/.../xsl-view/view.xsl` inserted raw keyword text into the
`query_string` fragment of a search link. A keyword such as `A&B` introduced a
new URL parameter, while quotes or backslashes corrupted the JSON query. All
three keyword link paths now escape the JSON string and URL-encode the whole
query. A rendered-link test checks that punctuation and Unicode round-trip to
the intended `tag.*` search filter.

## Marine phytoplankton database ISO export fails validation and has no abstract (2026-10-11)

The source MEF for UUID `1f7b7000-1cc3-428f-974d-a688398f51e0` has an empty
`gmd:dateStamp`, and its top-level `gmd:identificationInfo` precedes required
hierarchy/contact elements. Strict validation against the local ISO 19139
schema fails at `identificationInfo`. The identification abstract is also
empty. The source export remains unchanged; the EML migration explicitly
records the absent abstract because the local EML-GBIF profile requires one.

## MEF upload rejected when optional group is blank (resolved in source, 2026-10-11)

The `POST /srv/api/records` import handler validates the optional `group`
parameter as a workspace before starting the MEF import. When the UI submits
`group=""`, validation passed the empty value to `Integer.parseInt`, producing
`For input string: ""` and a 400 `unsatisfied_request_parameter` response
before any UUID handling mode runs. `checkGroupIsWorkspace` now skips validation
for a missing or blank group, and a regression test covers null, empty, and
whitespace values. Until this server change is deployed, omit the `group`
field from the multipart request or supply a valid workspace group ID.

## Resized attachment endpoint throws NPE for undecodable image content (resolved in source, 2026-10-17)

A GeoNetwork log during the Vegetation of Slovenia import/display showed
`ImageIO.read(inputStream)` returning `null` at
`AttachmentsApi.serveResizedImage`, then `ImageUtil.resize` dereferencing it at
line 60. The endpoint now returns HTTP 415 for unsupported or malformed image
content and logs the record UUID and attachment filename. Tests cover non-image bytes, a
truncated PNG, and successful resizing of a valid PNG. Both packaged JPEGs are
valid and decode with the local JDK; the old log did not include the request
path, so the specific attachment served by the affected catalogue remains
unidentified.

## Vegetation of Slovenia source ISO export fails strict validation (2026-10-11)

The supplied ISO 19139 record for UUID `89ce7bbf-cf1b-4fe8-9ef9-70c817bc3789`
fails the repository's strict `gmd.xsd`: required top-level elements are
missing or out of order before `gmd:identificationInfo`, including the
metadata contact and `dateStamp`. The source export remains unchanged. Its
EML-GBIF migration validates against the local profile; the ISO record should
be corrected if it continues to be maintained in ISO form.

## Amphipoda EML view hid the second image and showed raw distribution URLs (resolved in source, 2026-10-04)

The first converted package carried both ISO browse images but the EML view
rendered only its single GBIF logo field. Its distribution template also showed
plain, encoded URLs instead of the source record's download and link cards.
The rebuilt package identifies the second packaged image in `additionalInfo`
and supplies readable distribution descriptions. The EML formatter now shows
both overviews and grouped resource cards. Deploy the updated formatter and
web UI styling, then reimport the rebuilt MEF for those changes to appear in a
hosted catalogue.

## Amphipoda trait dataset source ISO lacks required metadata (2026-10-04)

The supplied ISO 19139 export for UUID `f39e56c2-65d4-43d2-b5f2-e707229777bf`
fails strict `gmd.xsd` validation: `gmd:identificationInfo` appears before a
required top-level `gmd:contact`, and the record also has no top-level
`gmd:dateStamp`. Its only citation date, `2024-02-10`, is explicitly a creation
date, not a confirmed dataset publication date. The source remains unchanged;
the converted EML-GBIF record validates and omits `pubDate`. Correct the ISO
record if it continues to be maintained, and confirm a dataset publication date
with the owner before adding one to EML.

## EML organisation-only creators showed as blank contact cards (resolved in source, 2026-10-03)

The EML formatter created a Contacts card for an organisation-only `creator`
but rendered its title only when `individualName` existed. It also displayed
no role when the role was implied by the EML element (`creator`, `contact`, or
`metadataProvider`). The Karst microbiological database therefore showed two
cards under `IZRK ZRC SAZU`, one appearing empty. The formatter now shows the
organisation name and implicit role while keeping explicitly recorded roles.
The regression test covers the organisation-only creator. Deploy the updated
formatter for the correction to appear in a hosted catalogue.

## Karst microbiological database source ISO lacks required metadata (2026-10-03)

The supplied ISO 19139 export for UUID `28b6a390-8254-479b-ba55-c70f59e121d6`
fails the repository's strict `gmd.xsd` validation: `gmd:identificationInfo`
appears where a required top-level `gmd:contact` is expected, and the record
also has no top-level `gmd:dateStamp`. Its citation date is empty. The source
remains unchanged; the EML-GBIF migration validates against the local profile.
Correct the ISO record if it remains in use, and confirm a dataset publication
date with the owner before adding an EML `pubDate`.

## EML Additional information lost its line structure (resolved in source, 2026-10-03)

The portal formatter collapsed newline-separated ISO notes into one paragraph,
making their labels hard to read. It also failed when `additionalInfo` contained
more than one `para`, because the creation-date lookup passed multiple nodes to
XPath `string()`. The formatter now renders ISO notes as labeled rows, retains
ordinary paragraphs as prose, and reads the date across multiple paragraphs.

## ISO metadata contact appeared only as plaintext (resolved in source, 2026-10-03)

The Postojna ISO export has a metadata contact with only
`magdalena.aljancic@zrc-sazu.si`; its individual name, organisation, and role
are empty. The first migration put the email in `additionalInfo` and the
Contacts view omitted it. The user confirmed the name Magdalena Aljančič.
The regenerated MEF now puts her name and source email in the existing EML
`metadataProvider` field, which the Contacts formatter already renders. The
plaintext copy and the temporary email-only profile exception were removed.

## EML portal omitted categories and conflated creation dates (resolved in source, 2026-10-03)

The EML portal's Technical information section displayed only values from EML
XML. GeoNetwork supplies catalogue categories and the record creation date
separately in the formatter's `/root/info/record` data, and the Postojna MEF
preserves both in `info.xml`. The portal formatter initially labeled the
record's 2022 creation date simply "Creation date", which confused it with the
ISO citation's 2009 creation date. The portal now shows only the ISO citation
creation date and the categories; the 2022 catalogue timestamp remains in the
MEF for provenance. Deploy the updated formatter for the change
to appear in a hosted catalogue; the MEF alone cannot update deployed view
code.

## Postojna minisites source ISO export lacks `dateStamp` (2026-10-03)

The supplied ISO 19139 export for UUID `8306e789-a3e5-40b2-aad4-aa69436a063c`
fails the repository's strict `gmd.xsd` validation: after the top-level
`gmd:contact`, `gmd:identificationInfo` appears where a required
`gmd:dateStamp` is expected. The source remains unchanged. Its EML-GBIF
migration validates against the local EML profile, but the ISO record should be
corrected if it continues to be maintained in ISO form.

## Local GeoNetwork setup for testing the feature-catalogue citation fix

Use this checklist when opening a fresh terminal. Java selection is per terminal unless it is configured in the shell startup file; the build itself only needs to be repeated after changing source code or when generated build output is missing.

### 1. Select Java 11 in the new terminal

From the repository root:

```sh
export JAVA_HOME="$(/usr/libexec/java_home -v 11)"
export PATH="$JAVA_HOME/bin:$PATH"
java -version
```

Confirm the output says Java 11. The previous Java 25 selection caused `IO` name ambiguity during compilation.

### 2. Build backend modules when needed

From the repository root, build `services` and its reactor dependencies together:

```sh
mvn -pl services -am clean install -DskipTests
```

Do not resume only at `:gn-services` with `-rf`; that skips rebuilding its dependencies and can leave Maven using an incomplete/stale `gn-core` JAR. This is the cause of the `SettingManager` / `Settings` not found error seen on 2026-10-02. You do not need to repeat this build just because you opened another terminal.

### 3. Make the schema formatter changes available to the web app

In a separate terminal (or after the build), from the repository root:

```sh
cd "$(git rev-parse --show-toplevel)/web"
mvn process-resources -DschemasCopy=true
```

Use the `-DschemasCopy=true` property, not `-PschemasCopy` (there is no such Maven profile). This copies local schema plugin changes into the web app resources.

### 4. Start the local catalogue

Keep this terminal open while testing:

```sh
# If this is a fresh terminal, first run:
cd "$(git rev-parse --show-toplevel)/web"
mvn jetty:run -Penv-dev
```

Open <http://localhost:8080/geonetwork>. The development profile disables the JavaScript cache so local UI changes are visible. The default local login is `admin` / `admin`.

### 5. Check the citation link

Open or import a local record that contains the feature-catalogue citation/online resource being tested. In its full record view, inspect the citation link. For an external `uuidref` beginning with `http://` or `https://`, it should point directly to that external URL; internal UUID references should continue to use the local `/srv/api/records/{uuid}` route. The local server will not automatically contain the remote catalogue's record just because its UUID is known.

### Troubleshooting notes

- If the web UI reports missing Bootstrap or `bootstrap-table` assets, initialize the three web UI submodules once from the repository root:

  ```sh
  git submodule update --init web-ui/src/main/resources/catalog/lib/bootstrap-table web-ui/src/main/resources/catalog/lib/style/bootstrap web-ui/src/main/resources/catalog/lib/style/font-awesome
  ```

  If Git aborts with `refs/files-backend.c ... existing refs`, update/use a stable Git version and retry after moving the failed partial submodule checkout and its matching `.git/modules/...` directory aside.
- On Apple Silicon, if Maven fails in `prettier-maven-plugin` with `Bad CPU type in executable`, its bundled Node executable is x86-only. Use Rosetta for that build step or avoid rebuilding `web-ui` when only backend/schema changes are needed.
- Long EML abstracts can contain several citation URLs. The record header now splits and links each HTTP(S) URL independently via `linkifyUrls`; rebuild/copy the `web-ui` resources and deploy the UI change for it to appear on the online catalogue. Importing the metadata alone does not update this renderer.

## Copepoda metadata semantics

The source metadata describes “species abundance,” but the supplied workbook is a presence-by-cave matrix (`x` marks) with `N drips` and `N caves` summaries. It does not provide numeric per-taxon abundance values. The pilot occurrence CSV therefore represents only recorded presences; blank cells are not interpreted as confirmed absences. Consider updating the description/title with the data owner if it is intended to describe these exact data.

The data owner confirmed these source corrections: `Bryocamptus n.sp. 1` occurs in Pivka jama and Škocjanske jame (`N caves=2`); `Bryocamptus n.sp. 2` occurs in Pološka, Snežna, and Zadlaška jama (`N caves=3`); the Škocjanske jame `TOTAL` is 9 after adding the confirmed presence; and the `TOTAL` for Zadlaška jama is 3. The corrected workbook copy is `/private/tmp/outputs/copepod-correction-20261002/Epikarst.Copepoda_13caves_taxonomy_corrected.xlsx`; the downloaded source workbook remains unchanged.

The current EML-GBIF MEF package is at `/private/tmp/outputs/copepod-import-20261002/copepoda-eml-gbif-preserved.mef`. It preserves the original UUID, ten keywords, both public images, categories, source access privileges, and the original online data link. It omits the extra occurrence and summary CSV attachments from the earlier conversion so the migration stays close to the ISO record. The taxon browser, keyword links, abstract linkification, and local browse-image resolution depend on deploying the corresponding schema and web UI changes; importing the record alone cannot deploy formatter/UI code.

The metadata authoring script had added the literal placeholder `keywordThesaurus=Not specified in source metadata`; it is omitted so the record displays just its keyword list. The local EML-GBIF profile now permits free-text keywords without inventing a thesaurus. The original ISO abstract was one long character string; the EML package separates the summary, related-literature heading, and each citation into EML paragraphs while preserving the normalized text. It excludes the owner correction note from the import and uses the packaged browse-image filename in EML-Gbif `resourceLogoUrl`. The ISO citation date `2022-10-15` was mapped to EML `pubDate` and confirmed by the data owner. The original resource format and feature-catalogue link are retained in `additionalInfo`.

## EML-Gbif record view formatter compilation (resolved)

The EML-Gbif `xsl-view` formatter referenced `eml-fn:party-key`, `party-name`, `party-roles`, `field-key`, and `get-eml-citation` without definitions. Opening a newly imported EML record therefore failed while compiling its view stylesheet. Added the shared EML citation/helper stylesheet used by both formatter views. Regression coverage is in `schemas/eml-gbif/src/test/python/test_formatter_citation.py`.

## Portal logos and Copepoda thumbnail missing after deployment (2026-10-02)

The current portal templates reference project logo files under
`catalog/views/default/images/izrk/projects/` and a footer logo at
`catalog/views/default/images/izrk/footer-logo.png`, but the source image folder
contains only `favicon.png` and `logo.png`. `package-deploy.sh` copies the folder
as-is, so the missing project/footer assets cannot appear after a rebuild. The
required source artwork must be recovered/provided before these references can
work; do not invent replacement institutional logos.

The original MEF export contains the copepod browse image as a public attachment.
The import builder initially omitted it, leaving `resourceLogoUrl` pointing to a
dead attachment URL. The builder now includes that exact source image in the
MEF's `public/` directory and manifest. A separate `image.png` in the original
export is also included to preserve the original public attachments. Live
status could not be checked from this environment: DNS resolution for
`metadata.izrk.zrc-sazu.si` fails here, and the local Docker daemon socket is
unavailable.

The EML portal formatter places descriptive keywords below the image in the
right column, as requested for the migrated record. The abstract stays below
the title in the main column.

## Original Copepoda ISO 19139 export fails strict schema validation (2026-10-02)

The source MEF for UUID `c7710542-10ea-43e8-b4d7-9bdd3d559905` lacks three
required ISO 19139 elements: top-level `gmd:contact`, top-level `gmd:dateStamp`,
and `gmd:MD_DataIdentification/gmd:language`. The local `gmd.xsd` rejects the
original export. A temporary validation probe passed after copying the existing
identification contact and metadata language into their required positions and
using the export's change date as `dateStamp`. This applies to the ISO source;
the EML-GBIF target package validates against the customized local profile.
GeoNetwork's actual import behavior remains to be checked on a running instance.

## EML-Gbif keyword filters returned no records (resolved in source, 2026-10-02)

The EML-Gbif record view links keywords to `tag.*` search filters, but its index
stylesheet emitted only the legacy `keyword` and `subject` fields. An imported
EML record could therefore show a keyword while a click on it returned no
records, including the current record. The index stylesheet now emits the
structured `tag`, `tagNumber`, and `allKeywords` fields used by GeoNetwork's
search. Existing EML records must be reindexed after this change is deployed;
the fix cannot alter their already stored search documents.

The Copepoda taxonomy reference also used uppercase order names while the EML
coverage used title case. The formatter's case-sensitive merge left Cyclopoida
and Harpacticoida under “Unlinked names” as well as in their linked branches.
The merge now compares normalized names without case, and the packaged record
renders two order branches with no unlinked names.

## EML-Gbif portal abstract absent from record view (resolved in source, 2026-10-02)

The Copepoda MEF contains the complete abstract as 15 EML paragraphs, but the
portal record view did not visibly show it. The portal now renders a labeled
Abstract section directly beneath the title using its existing paragraph and
link renderer. The keyword list sits beneath the image in the right column;
the remaining sections keep their positions. Deploy the updated formatter to
show this on the hosted catalogue.

## EML-GBIF profile required an unknown publication date (resolved in source, 2026-10-03)

The ISO 19139 record `1b83ee14-6498-4f9b-a297-eb1692095c1a` has an empty
citation date. Its 2017 journal reference is a related paper, not a confirmed
dataset publication date. The local EML-GBIF XSD required `pubDate`, which
would force a fabricated date or reject a faithful conversion. The profile now
allows `pubDate` to be omitted, with a schema regression test. The converted
record leaves it absent. Copy the updated schema into any deployed catalogue
before importing this package.

## Škocjanske jame source ISO export fails strict validation (2026-10-03)

The original ISO 19139 XML for UUID `1b83ee14-6498-4f9b-a297-eb1692095c1a`
fails the repository's `gmd.xsd`: `gmd:identificationInfo` appears where the
schema still requires a top-level `gmd:contact`. The original export is kept
unchanged; the converted EML-GBIF XML validates against the updated local
profile. The source defect should be corrected in the ISO record if that record
continues to be maintained.
