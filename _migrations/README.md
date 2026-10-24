# EML migration checks

Run the full suite from the repository root after building the web application:

```sh
export SAXON_JAR="$PWD/web/target/geonetwork/WEB-INF/lib/saxon-9.1.0.8b-patch.jar"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s _migrations -p 'test_*.py' -v
```

The suite uses `xmllint`, Java, the packaged Saxon JAR, and compiled GeoNetwork
classes for schema and stylesheet checks. The Linux QA workflow verifies these
dependencies and runs this command for every pull request.

The committed MEFs are always checked. Additional comparisons with the
original ISO exports run when these environment variables point to the
extracted **record directory** containing `info.xml` and `metadata/metadata.xml`:

| Variable | Record |
| --- | --- |
| `KARST_MICROBIOLOGY_ISO_SOURCE` | Karst microbiological database |
| `MARINE_PHYTOPLANKTON_ISO_SOURCE` | Marine phytoplankton database |
| `POSTOJNA_ISO_SOURCE` | Postojna minisites |
| `POSTOJNA_PLANINA_LTER_ISO_SOURCE` | Postojna-Planina LTER |
| `VEGETATION_SLOVENIA_ISO_SOURCE` | Vegetation of Slovenia |

These original exports are not committed. Source comparison tests are skipped
when their export is unavailable; all package checks still run.

Three builders need the path to an extracted source record directory, because
the source MEFs are not checked in. Their output path defaults to the matching
MEF in `_migrations/`:

```sh
python3 _migrations/build_marine_phytoplankton_eml.py --source /path/to/1f7b7000-1cc3-428f-974d-a688398f51e0
python3 _migrations/build_postojna_planina_lter_eml.py --source /path/to/d3011b1e-3aa5-4b61-a3bc-94da67f582c8
python3 _migrations/build_vegetation_slovenia_eml.py --source /path/to/89ce7bbf-cf1b-4fe8-9ef9-70c817bc3789
```

## Pollen taxonomy migration

`build_pollen_taxonomy.py` nests parent relationships within an exported pollen
MEF so the formatter can read them from the record. It requires the current MEF
for UUID `9f64b6e3-22be-4f17-9cc0-8658c7817867` and a CSV with these columns:

```text
child_rank,child_name,parent_rank,parent_name,source_reference
```

The checked-in `pollen-taxonomy.csv` cites GBIF taxon pages for the three
parent links formerly supplied by the formatter. Taxon names present in the
export are matched by exact rank and name; absent names are added from these
cited relationships to the EML classification. The builder rejects ambiguous
taxa, duplicate parents, existing nested children, and cycles; it preserves
all other MEF members. It accepts either an exported MEF archive or its
extracted record directory. The generated `_migrations/pollen-eml-gbif.mef`
was built from the September 2026 export in Downloads and validated against
the local EML-GBIF schema. It also normalizes `packageId` to the record UUID,
removes source-catalogue IDs and metrics from `info.xml`, and regenerates root
index files without the source database ID.

To rebuild it from the attached extracted export:

```sh
python3 _migrations/build_pollen_taxonomy.py /path/to/9f64b6e3-22be-4f17-9cc0-8658c7817867 \
  _migrations/pollen-eml-gbif.mef \
  --relationships _migrations/pollen-taxonomy.csv
```
