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
Current verification counts and browser/API checks are recorded in
`reports/upgrade-20260917.json`; the earlier repair report is historical. The
current catalogue has 431 records and templates. The deliberately deleted
`Copy of ...` records have not been restored. After copying the stopped data snapshot, run
`sha256sum -c reports/upgrade-20260917-data.sha256` before starting the containers
to verify the transferred H2 database and Elasticsearch files.

To refresh this folder after a local build, run from the repository root:

```bash
./docker/izrk/scripts/package-deploy.sh
```

Use `--build-war` to rebuild the application before packaging. The current
package uses GeoNetwork `4.4.13-SNAPSHOT`, merged from upstream `main` at
`34225caa440be37162ed93d895cacd290c49e48b` on 17 September 2026.

The EML portal view uses the same card and section layout as the other dataset
standards. Standalone `/srv/api/records/<uuid>` HTML keeps its existing layout.
Both show all taxon names in compact lists grouped by rank, with parent lineages,
common names and identifiers retained. The portal requests `view=portal`; the
standalone and legacy fragment views continue to use `view=default`.

Keep the Dockerfile, Compose file, scripts and this README in Git. The WAR,
`runtime/`, checksum manifest, verification reports and mutable `data/` contents
are generated or deployment state and are ignored. The folder is therefore a
mixture of deployment source and packaged output, not wholly a build artifact.

Pre-upgrade data and application snapshots are in
`data/backups/upstream-20260917`. Upgrade and layout verification results are in
`reports/upgrade-20260917.json`; transfer checksums for the final stopped data
are in `reports/upgrade-20260917-data.sha256`.
