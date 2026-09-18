# IZRK GeoNetwork Build And Deployment

## Build

```bash
docker/izrk/scripts/package-deploy.sh --build-war
docker/izrk/scripts/build-image.sh
```

This produces `web/target/geonetwork.war` and the Docker image
`izrk-geonetwork:4.4.13-SNAPSHOT`. To build and package without a Docker daemon:

```bash
docker/izrk/scripts/package-deploy.sh --build-war
```

## Run Locally

```bash
mkdir -p docker/izrk/data/elasticsearch docker/izrk/data/geonetwork docker/izrk/data/geonetwork-home
GEONETWORK_PUBLIC_URL=http://localhost:8081 \
  docker compose -p izrk -f docker/izrk/docker-compose.yml up -d --build
```

The compose file uses bind mounts under `docker/izrk/data`, not Docker named
volumes. Run Compose from a checkout visible to the Docker daemon so those
bind mounts refer to the real project folders.

Open `http://localhost:8081/srv/eng/catalog.search`.

The deployment compose file sets `GEONETWORK_PUBLIC_URL` to the production
origin `https://metadata.izrk.zrc-sazu.si` by default. Override it for another host, for
example:

```bash
GEONETWORK_PUBLIC_URL=http://catalog.example.org:8080 \
  docker compose -f docker/izrk/docker-compose.yml up -d --build
```

Before Tomcat starts, the GeoNetwork container synchronizes this origin into
the H2 server settings and rewrites existing loopback `/srv/` API links and the
misspelled `metadata.izrk.zrcsazu.si` catalogue origin in metadata. Cached formatter
HTML is archived on deployment/origin changes. If starting with a brand-new H2
database, restart the `geonetwork` service once after its first initialization
so the same synchronization can run against the created database.

## Catalogue Data

The deployment already contains the current catalogue in its data directories.
The original import is complete; there is no `_migration` dependency or import
step during deployment or startup. Historical inputs and backups remain archives
and must not be used to restore deliberately deleted `Copy of ...` records.
Existing owner mappings include legitimate records owned by Žan Kafol.
Deploy the supplied snapshot as described below.

## Move To Production

After packaging, copy the self-contained `docker/izrk` folder to the server.
The Dockerfile only needs files inside that folder. Stop the source and target
services before transferring a database snapshot, and keep all three data
directories together. Then run on the server:

```bash
cd docker/izrk
docker compose up -d --build
```

See `docker/izrk/README.md` for the repaired September 2026 catalogue snapshot,
backups, transfer checksums and the distinction between tracked deployment
source and ignored build artifacts.

The simple Docker setup uses GeoNetwork's bundled H2 database. The database file
is stored in `docker/izrk/data/geonetwork-home`, GeoNetwork data is stored in
`docker/izrk/data/geonetwork`, and Elasticsearch data is stored in
`docker/izrk/data/elasticsearch`. Keep those folders together with the compose
file for a portable deployment. For a larger production deployment, replace H2
with PostgreSQL before public launch.
