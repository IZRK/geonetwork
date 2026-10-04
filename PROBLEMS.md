# Problems and follow-up

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
