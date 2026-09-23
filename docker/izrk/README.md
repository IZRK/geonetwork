# IZRK GeoNetwork Deployment

This folder is the self-contained production deployment. Copy the whole `docker/izrk`
folder to the server and run from inside the copied folder:

```bash
./scripts/fix-permissions.sh
docker compose up -d --build
```

Durable catalogue data is stored in real bind-mounted folders:

- `data/geonetwork` for GeoNetwork configuration and uploads
- `data/geonetwork-home` for the H2 catalogue database and container root home
- `data/elasticsearch` for the rebuildable search index

GeoNetwork and Elasticsearch use Docker's `unless-stopped` restart policy so
containers not manually stopped return when the Docker daemon starts after a
host reboot. The host must also start Docker at boot (for example, enable
`docker.service` on a systemd Linux server). After changing this policy, apply
it without rebuilding the image with `docker compose up -d --no-build` from
this folder; Compose recreates containers when service configuration changes
and preserves their bind-mounted data.

For the revised September 20 portal, record layout and taxonomy update, upload the application-only
archive `izrk-deploy-20260920-polish.tar.gz` and its `.sha256` file into the server's
**existing IZRK deployment folder**. From that folder run:

```bash
sha256sum -c izrk-deploy-20260920-polish.tar.gz.sha256
tar -xzf izrk-deploy-20260920-polish.tar.gz
docker compose up -d --build
```

The archive contains the Docker build files, WAR, runtime overlays and startup
scripts. It deliberately contains no `data/`, backups or migration inputs.
Keep the server's existing `data/` directories in place. This update requires no
catalogue import, owner correction or reindex; startup refreshes application
configuration and generated caches. Do not replace current data with the older
repair snapshots described below.

To prepare a new application upload archive from the repository, run
`./docker/izrk/scripts/package-upload.sh`. It refreshes the deployment folder and
creates a timestamped archive and checksum beside `docker/izrk`. An optional
first argument specifies the output archive path.

The catalogue import is complete. The supplied data directories are the current
catalogue; deployment and startup do not read `_migration` or run an import.
Historical inputs and backups are retained for reference. Deliberately deleted
`Copy of ...` records must not be restored from them. Record owners include Žan
Kafol where the record-specific mapping assigns ownership to him.

For an application-only update, keep the existing `data/geonetwork` and
`data/geonetwork-home` folders. The Elasticsearch container writes as uid `1000`, so the
Compose file runs `elasticsearch-permissions` before startup to repair copied
folder ownership. `scripts/fix-permissions.sh` is the manual equivalent.

The default public origin is `https://metadata.izrk.zrc-sazu.si`. Startup writes
`GEONETWORK_PUBLIC_URL` to the H2 server settings and repairs stored catalogue
links using the old misspelled origin. It also archives cached formatter HTML
when the deployment or public origin changes, so pages regenerate with current
links. Set `GEONETWORK_PUBLIC_URL` explicitly only when using a different origin.

On a deployment change, startup also refreshes the bundled standard schema
plugins, shared XSL formatters and index configuration from the WAR. Previous
copies are archived under `data/geonetwork/config-backups`. Keep IZRK schema
changes in the EML plugin or deployment source so they are included in builds.

The September 2026 catalogue repair includes corrected data files as well as
application changes. To deploy that snapshot, stop the server's containers with
`docker compose down`, back up its deployment folder, and replace the deployment
and its three data directories together. Copy the data while both installations
are stopped, then run `docker compose up -d --build`. Copying just the WAR leaves
the stale owner/category index in place. Pre-repair local snapshots are in
`data/backups/repair-20260917`.
The September 17 verification counts and browser/API checks are recorded in
`reports/upgrade-20260917.json`; the earlier repair report is historical. The
current catalogue has 431 records and templates. The deliberately deleted
`Copy of ...` records have not been restored. The dated data checksums describe
that earlier snapshot, not catalogue files after subsequent application runs.

The September 18 data correction restores the LifeWatch abstract for EML record
`9f64b6e3-22be-4f17-9cc0-8658c7817867` in both H2 and Elasticsearch. The
original May 27 import contained the abstract; a later May 28 record update had
replaced it with an empty paragraph, so no importer or formatter change is
required. A pre-correction H2 copy is retained beside the live database as
`gn.mv.db.pre-abstract-repair-20260918T083240Z`.

To refresh this folder after a local build, run from the repository root:

```bash
./docker/izrk/scripts/package-deploy.sh
```

Use `--build-war` to rebuild the application before packaging. This uses an
incremental Maven package so normal UI and formatter changes reuse existing
artifacts. Use `--build-war --clean-war` only after dependency/version changes,
switching checkouts, or an integrity-check failure. The packaging script checks
the WAR for stale conflicting libraries and retries with a clean build only
when needed. The current package uses GeoNetwork `4.4.13-SNAPSHOT`, merged from upstream `main` at
`34225caa440be37162ed93d895cacd290c49e48b` on 17 September 2026.

The revised portal uses a white project-logo section, description previews for
records without thumbnails, consistent record grids and aligned icon/label pairs.
Long descriptions expand on demand, organization contact groups remain browsable,
and native contacts show both names and email addresses. Missing organizations
no longer produce an `undefined` heading. Citation formats use readable buttons;
copying and downloading preserve the selected citation content.

The attachment `diversity-12-00269-ag-550 copepoda.jpg` contains WebP bytes despite
its extension. The deployment includes the pure-Java TwelveMonkeys ImageIO WebP
reader (3.13.1) in Tomcat's shared `lib/`, so the existing thumbnail API can decode
it without replacing the attachment or changing GeoNetwork core. The six JARs
are pinned in `scripts/imageio-artifacts.json`, verified by SHA-256 during
packaging, and included in the archive. Production builds need no dependency
download. Their embedded BSD licenses are retained. See the
[upstream deployment notes](https://github.com/haraldk/TwelveMonkeys#deploying-the-plugins-in-a-web-app).

Record pages share the IZRK section styling and compact, grouped contacts.
The EML portal uses the native citation, sharing and similar-dataset components;
its full view groups metadata into tabs. Standalone `/srv/api/records/<uuid>`
HTML uses the same blue footer content as the portal. The packaging script
generates this footer overlay from the portal template without editing the
upstream XSL skin.
All three EML views share a compact, expandable taxonomy tree. Recorded parent
relationships take priority, and every recorded name, common name and identifier
is retained. The classification has a bounded scrolling area to keep long lists
from lengthening the page. Unlinked names are ordered from broader to narrower
ranks without implying parent relationships.

The pollen record `9f64b6e3-22be-4f17-9cc0-8658c7817867` also has an explicitly
labelled, frozen GBIF reference classification in the plugin's
`formatter/taxonomy-reference.xml`. This display layer leaves catalogue XML and
the search index unchanged, and makes no network requests during rendering.
It is scoped to the record UUID and exact recorded names/ranks. Nested source
classifications and explicit source taxon identifiers bypass enrichment.
The 20 September 2026 snapshot matches 150 of the 165 recorded entries; the
remaining 15 are shown separately with the reason they were not resolved.
Queries use the Plantae context established by this pollen/plant dataset.
Fuzzy matches, conflicting classifications, nonaccepted names and rank
mismatches cannot supply inferred parents. Original synonym names are retained.

To review or regenerate a reference from a CSV with `UUID` and `DATA` columns
(EML XML), run from the repository root:

```bash
python3 schemas/eml-gbif/scripts/build_taxonomy_reference.py records.csv \
  schemas/eml-gbif/src/main/plugin/eml-gbif/formatter/taxonomy-reference.xml \
  --cache /path/to/gbif-response-cache --kingdom Plantae
```

Only provide a kingdom established by those records; omit the option for a mixed
catalogue. Retain the response cache for provenance and use a new cache directory
for a fresh snapshot. Review changes before packaging. This is a maintenance
command, not a startup step. It does not import or update records.

The portal requests `view=portal`; the standalone and legacy fragment views use
`view=default`. The IZRK home facet template adds category/resource icons while
retaining GeoNetwork's facet links, translations, counts and configured decorators.
The portal theme preserves the project logo order and existing footer content.
Their original images are packaged under `catalog/views/default/images/izrk`
instead of requiring Imgur hotlink access.

Keep the Dockerfile, Compose file, scripts and this README in Git. The WAR,
`runtime/`, checksum manifest, verification reports and mutable `data/` contents
are generated or deployment state and are ignored. The folder is therefore a
mixture of deployment source and packaged output, not wholly a build artifact.

Pre-upgrade data and application snapshots are in
`data/backups/upstream-20260917`. Upgrade and layout verification results are in
`reports/upgrade-20260917.json`.
