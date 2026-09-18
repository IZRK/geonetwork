#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p \
  "${ROOT_DIR}/data/elasticsearch" \
  "${ROOT_DIR}/data/geonetwork" \
  "${ROOT_DIR}/data/geonetwork-home"

# The official Elasticsearch image writes as uid 1000, group 0. When the
# deploy folder is copied as root, the bind-mounted index directory can become
# unreadable and Elasticsearch exits before GeoNetwork can index records.
chown -R 1000:0 "${ROOT_DIR}/data/elasticsearch"
chmod -R ug+rwX "${ROOT_DIR}/data/elasticsearch"

chmod -R u+rwX "${ROOT_DIR}/data/geonetwork" "${ROOT_DIR}/data/geonetwork-home"

echo "Fixed writable permissions under ${ROOT_DIR}/data"
