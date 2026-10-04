# Postojna-Planina LTER site: ISO 19139 to EML-GBIF

Source: extracted GeoNetwork MEF at
`/Users/vids/Downloads/d3011b1e-3aa5-4b61-a3bc-94da67f582c8/`.
Import package: `postojna-planina-lter-eml-gbif.mef` in this directory.
The source was read only. This is a research-site description, not a data
download; it follows the existing Postojna minisites EML-GBIF migration.

| Source field | EML-GBIF mapping |
| --- | --- |
| UUID `d3011b1e-3aa5-4b61-a3bc-94da67f582c8` | MEF UUID, EML `packageId`, and `alternateIdentifier` |
| Full title and abstract | Exact title; the nine source lines are separate `abstract/para` elements with normalized text unchanged |
| Six descriptive keywords | Six exact `keywordSet/keyword` values in source order, without a thesaurus placeholder |
| Operating organisation `IZRK ZRC SAZU` | Required `creator` organisation; no creator role is explicit in the source, so owner confirmation is needed for precise attribution |
| Matej Blatnik, `custodian`, and Magdalena Aljančič, `pointOfContact` | `associatedParty` with role `custodian`; `contact`, respectively, with both source emails and organisations |
| DEIMS URL in the abstract | Preserved in the abstract and made available as a `distribution/online` link labeled “DEIMS site record” |
| Extent `Postojna` and four bounding coordinates | `coverage/geographicCoverage`, exact values |
| Scope `Research sites`, status `onGoing`, metadata language `eng` | Scope in GBIF `hierarchyLevel` and `additionalInfo`; status and language in `additionalInfo` |
| Three ISO browse graphics | First packaged image in `resourceLogoUrl`; two additional packaged images referenced in `additionalInfo` for the local multi-image formatter |

The source citation date is empty, so the target has no `pubDate`. The source
has no structured taxonomic or temporal coverage, rights statement, or online
distribution entry. Names of animals remain in the abstract rather than being
promoted to unsupported taxonomic classifications. “Web Address: LTER Slovenia”
has no URL in the source and remains unchanged in the abstract.

The source `info.xml` creation date (`2022-08-29T11:06:31.943Z`), two categories,
and `all` group operations are preserved. `localId`, `siteId`, `siteName`, rating,
and popularity were removed as source-instance values. Root index files were
regenerated with the EML schema and no database ID.

## Public attachments

All three files named in the source manifest are present in the MEF with
identical SHA-256 digests:

| Filename | SHA-256 |
| --- | --- |
| `PPCS.JPG` | `6d21efba443cf33f1235b34b50e0aab3dfbf0f1fd733afd3187ed12da451594a` |
| `Planinska jama.JPG` | `611dd8f66b272e7a586642d21105a1d12149360abe200f2ea5e6f37f1afc5766` |
| `Zguba jama_tp.JPG` | `191e6667adce1e4b404ae5c286f9aaa33aa83b2e398144abfaf02999c4d479b5` |

The private directory and private manifest are empty in both source and target.

## Verification and deployment

- Target XML validates against the repository's local `eml.xsd`; ZIP integrity
  check passes.
- Four record-specific tests pass, covering content, access, attachment hashes,
  coverage, identity, and all six keywords in `tag.default`, `allKeywords`, and
  `tagNumber` after the actual index transform.
- The EML plugin suite passes 19 tests, including multi-image view rendering.
- The original ISO export fails strict local `gmd.xsd` because top-level
  `gmd:contact` and `gmd:dateStamp` are absent. This is recorded in `PROBLEMS.md`.
- No local GeoNetwork service responds at `localhost:8080`, so live image
  loading, record view, import, and keyword-link search remain unverified.

The hosted catalogue needs the current EML-GBIF formatter for all three images
to appear. Import this MEF after deploying that formatter, then check the site
record and keyword links. Importing under the original UUID may collide with
the ISO version; use the catalogue's intended replacement handling.
