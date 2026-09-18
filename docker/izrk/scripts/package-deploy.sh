#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="$(cd "${DEPLOY_DIR}/../.." && pwd)"

WAR_SOURCE="${REPO_DIR}/web/target/geonetwork.war"
WAR_TARGET="${DEPLOY_DIR}/geonetwork.war"

if [[ "${1:-}" == "--build-war" ]]; then
  (
    cd "${REPO_DIR}"
    # Upstream schema modules depend on each other's test JARs. Compile those
    # fixtures even when skipping test execution, including on a clean checkout.
    mvn -DskipTests -Dmaven.jar.forceCreation=true -Penv-prod,war -pl web -am package
  )
fi

if [[ ! -f "${WAR_SOURCE}" ]]; then
  echo "Missing ${WAR_SOURCE}. Run this script with --build-war or build the WAR first." >&2
  exit 1
fi

install -D -m 0644 "${WAR_SOURCE}" "${WAR_TARGET}"

mkdir -p \
  "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/templates" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/templates/recordView" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/js" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/style" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/images" \
  "${DEPLOY_DIR}/runtime/schema_plugins"

install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/templates/home.html" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/templates/home.html"
install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/templates/index.html" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/templates/index.html"
install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/templates/footer.html" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/templates/footer.html"
install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/templates/recordView/recordView.html" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/templates/recordView/recordView.html"
install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/js/CatController.js" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/js/CatController.js"
install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/style/srv_custom_style.less" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/style/srv_custom_style.less"
install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/style/izrk_record_style.less" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/style/izrk_record_style.less"
install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/less/gn_search_default.less" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/less/gn_search_default.less"

if [[ -d "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/images/izrk" ]]; then
  rm -rf "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/images/izrk"
  cp -a \
    "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/images/izrk" \
    "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/images/izrk"
fi

rm -rf "${DEPLOY_DIR}/runtime/schema_plugins/eml-gbif"
cp -a \
  "${REPO_DIR}/schemas/eml-gbif/src/main/plugin/eml-gbif" \
  "${DEPLOY_DIR}/runtime/schema_plugins/eml-gbif"

(
  cd "${DEPLOY_DIR}"
  {
    sha256sum geonetwork.war
    find runtime scripts -type f -print0 \
      | sort -z \
      | xargs -0 sha256sum
  } > deploy-manifest.sha256
)

echo "Prepared ${DEPLOY_DIR}"
