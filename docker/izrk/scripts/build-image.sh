#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DEPLOY_DIR"

test -f geonetwork.war
docker build \
  -f Dockerfile \
  -t izrk-geonetwork:4.4.13-SNAPSHOT \
  --build-arg GEONETWORK_WAR=geonetwork.war \
  .
