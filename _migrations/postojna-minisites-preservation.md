# Postojna minisites ISO 19139 → EML-GBIF

Source: supplied extracted GeoNetwork MEF export `8306e789-a3e5-40b2-aad4-aa69436a063c`. Output: `postojna-minisites-eml-gbif-preserved.mef` in this directory. The source was read only.

| Source | EML-GBIF package |
| --- | --- |
| UUID `8306e789-a3e5-40b2-aad4-aa69436a063c` | Same MEF UUID, EML `packageId`, and `alternateIdentifier` |
| Title `Postojnska jama (Postojna Cave) - bio-geo-chemo data (minisites 1-10)` | Exact title |
| Complete related-publications abstract | 14 EML paragraphs: heading and 13 citations; normalized text is identical |
| Six free-text keywords | All six exact values, in order, without a fabricated thesaurus |
| Citation date `2009-12-04`, type `creation` | Preserved with its type in `additionalInfo`; `pubDate` omitted because publication is unconfirmed |
| Owner/point of contact Tanja Pipan, IZRK ZRC SAZU, `tanja.pipan@zrc-sazu.si` | EML `contact`; also used for required `creator`, the closest available responsible party. Source does not explicitly identify a dataset creator; confirm this role with the data owner if precision is required. |
| ISO metadata contact `magdalena.aljancic@zrc-sazu.si`, no name or role | EML `dataset/metadataProvider` with email and user-confirmed name Magdalena Aljančič; shown in Contacts |
| Postojna extent: west `14.2005`, east `14.2098`, south `45.7802`, north `45.7841` | Exact geographic description and coordinates |
| Parent UUID, larger-work UUID, scope `Research sites`, status `onGoing` | Retained in `additionalInfo`; scope also in GBIF `hierarchyLevel` |
| Public image `IMG_20180404_103534948.jpg` | Copied byte for byte; `resourceLogoUrl` points to its packaged filename. SHA-256: `021ac5c356ca2f3148fae88a2e7a249839dc3dd3da614f4838704147e7700fb3` |
| Four categories and `all` / `Karst database` group operations | Preserved in `info.xml`, including group ownership and original creation date |

The source has no temporal or taxonomic extent, resource distribution URL, or rights statement; none was invented. Root `index.csv` and `index.html` are present, with EML schema/title information and no source-instance database ID. `info.xml` omits `localId`, `siteId`, `siteName`, rating, and popularity.

## Verification

- Local `eml.xsd` validation: passed.
- Archive integrity and attachment SHA-256 comparison: passed.
- Source-to-target content, coordinates, UUID, categories, privileges, and manifest tests: 4 passed.
- EML schema/formatter/index suite: 18 passed.
- Actual record index transform: all six keywords appear in `tag.default` and `allKeywords`; `tagNumber` is 6.
- The source ISO XML fails strict local `gmd.xsd` validation because its top-level `dateStamp` is absent. The source was not edited.
- No catalogue responded on `localhost:8080`; live record view, image loading, and keyword search remain unverified.

The EML portal's Technical information shows **Source citation creation date**
as `2009-12-04` from the ISO metadata. The MEF retains the catalogue record's
`2022-08-30T07:01:05.858Z` creation timestamp in `info.xml`, but the portal
does not display it. The formatter reads catalogue categories from GeoNetwork's
stored record information. This record lists `lifewatch`, `Karst DB`, `elter`,
and `RI-SI-LifeWatch`; GeoNetwork imports each category only if it already
exists in the target catalogue.

The source's metadata contact uses the existing EML `metadataProvider` field
and appears in Contacts, separate from the dataset contact. The ISO export
contains only the email address; the user confirmed the name Magdalena
Aljančič. No organisation or additional role was inferred. The address is no
longer repeated in free-text `additionalInfo`. The standard local `agentType`
applies, with no email-only exception or new metadata field.

To import this MEF, the target catalogue needs the current EML-GBIF profile that accepts an absent `pubDate`. Deploy the updated EML portal formatter to show the source citation date and categories. If the keyword index stylesheet has not been deployed there, deploy it and reindex existing EML records. Reimport this MEF to update an earlier import with Magdalena's confirmed name. Importing this package does not update deployed formatter or index code.
