# Karst microbiological database: ISO 19139 to EML-GBIF

Source: extracted GeoNetwork MEF at
`/Users/vids/Downloads/28b6a390-8254-479b-ba55-c70f59e121d6/`.
Output: `karst-microbiological-database-eml-gbif-preserved.mef`.
UUID and EML package ID: `28b6a390-8254-479b-ba55-c70f59e121d6`.

| Source | EML-GBIF result |
| --- | --- |
| Title, four abstract paragraphs, and nine keywords | Preserved verbatim after whitespace normalization. The DOI and request-only data contact remain in the abstract. |
| `IZRK ZRC SAZU`, named custodian Janez Mulec, and his email | The institute is the required EML creator because the abstract says the database was created there. Janez is the EML contact and an associated party with role `custodian`. The source does not identify an individual creator. |
| ISO language `eng` | `dataset/language=eng`; EML `xml:lang=en`. |
| ISO extent with blank description and four coordinates | Coordinates retained exactly. `Slovenia`, an exact source keyword, supplies the profile-required geographic description. |
| Empty ISO citation date | No `pubDate`; the abstract's 2017 database-creation statement is not a publication date. |
| ISO hierarchy `Services and databases`; status `onGoing` | Hierarchy copied to GBIF metadata and both source values retained in `additionalInfo`. |
| Browse image `20230516_100336.jpg` | Byte-for-byte public attachment, retained manifest entry, and `resourceLogoUrl` pointing to the packaged filename. SHA-256: `8cf4fac10f0dc528f8487cacb3cbc8ce30cad6afe0a03e7622728efa08961f1a`. |
| Five categories; public view, download, dynamic, and featured privileges | Preserved in `info.xml`, along with UUID and original catalogue creation date. Source-instance IDs and metrics were removed. |

The source has no taxonomic or temporal coverage and no populated distribution
link. The acknowledgment DOI in the abstract is a citation, not a data-download
URL. The source ISO XML fails strict `gmd.xsd` validation because it lacks the
required top-level contact and date stamp; it was not modified.

Verification: the converted XML passes the repository EML XSD; four migration
tests pass, including archive contents, access, byte hashes, and search index
fields (`tag`, `tagNumber=9`, `allKeywords`). The 18 EML plugin tests pass.
Live catalogue rendering and keyword-link behavior remain unverified because
the local GeoNetwork endpoint could not be reached from this environment.
Import the MEF into the intended catalogue, then check the image and keyword
links in its record view. A deployed schema older than the local optional
`pubDate` profile must be updated before import.

The local EML formatter now gives the organisation-only creator its own named
card and `Creator` role. The separate Janez Mulec card shows his contact and
custodian roles. These two entries reflect two distinct EML parties; deploy
the formatter change to update an existing catalogue view. The MEF itself did
not need to change for this display fix.
