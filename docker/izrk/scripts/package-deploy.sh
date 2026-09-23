#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="$(cd "${DEPLOY_DIR}/../.." && pwd)"

WAR_SOURCE="${REPO_DIR}/web/target/geonetwork.war"
WAR_TARGET="${DEPLOY_DIR}/geonetwork.war"

BUILD_WAR=false
CLEAN_WAR=false
for arg in "$@"; do
  case "${arg}" in
    --build-war)
      BUILD_WAR=true
      ;;
    --clean-war)
      CLEAN_WAR=true
      ;;
    *)
      echo "Usage: $0 [--build-war] [--clean-war]" >&2
      exit 2
      ;;
  esac
done

if [[ "${CLEAN_WAR}" == true && "${BUILD_WAR}" != true ]]; then
  echo "--clean-war requires --build-war" >&2
  exit 2
fi

python3 - \
  "${REPO_DIR}/web-ui/src/main/resources/WEB-INF/classes/web-ui-wro-sources.xml" \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/module.js" \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/templates/recordView/type-dataset.html" \
  "${REPO_DIR}/schemas/eml-gbif/src/main/plugin/eml-gbif/formatter/xsl-view/view.xsl" <<'PY'
import sys
import xml.etree.ElementTree as ET

wro_path, module_path, iso_template_path, eml_formatter_path = sys.argv[1:]
root = ET.parse(wro_path).getroot()
sources = [source.get("webappPath", "") for source in root.iter()]
if any("leaflet" in source.lower() or "extentmap" in source.lower() for source in sources):
    raise SystemExit("WRO check failed: a separate Leaflet extent-map implementation is still loaded")

with open(module_path, encoding="utf-8") as module:
    if "izrk_extent_map" in module.read():
        raise SystemExit("WRO check failed: search module still requires ExtentMap")

with open(iso_template_path, encoding="utf-8") as template:
    if 'data-gn-data-preview="mdView.current.record"' not in template.read():
        raise SystemExit("Map consistency check failed: ISO does not use GeoNetwork's native map")

with open(eml_formatter_path, encoding="utf-8") as formatter:
    markup = formatter.read()
    if 'data-gn-data-preview="mdView.current.record"' not in markup:
        raise SystemExit("Map consistency check failed: EML does not use GeoNetwork's native map")
    if "gn-img-extent" in markup or "leaflet" in markup.lower():
        raise SystemExit("Map consistency check failed: EML still emits a static or Leaflet map")
print("Map consistency check: both standards use GeoNetwork's native interactive map")
PY

verify_war_integrity() {
  python3 - "${WAR_SOURCE}" <<'PY'
import collections
import re
import sys
import zipfile

path = sys.argv[1]
with zipfile.ZipFile(path) as archive:
    entries = set(archive.namelist())
    jars = [
        name.rsplit("/", 1)[-1][:-4]
        for name in entries
        if name.startswith("WEB-INF/lib/") and name.endswith(".jar")
    ]

if "WEB-INF/web.xml" not in entries:
    raise SystemExit("WAR integrity check failed: WEB-INF/web.xml is missing")

patterns = {
    "GeoNetwork": ("gn-", re.compile(r"^(.*)-(\d+\.\d+\.\d+(?:-SNAPSHOT)?)$")),
    "GeoTools": ("gt-", re.compile(r"^(.*)-(\d+\.\d+)$")),
    "Log4j": ("log4j-", re.compile(r"^(.*)-(2\.\d+\.\d+)$")),
}
conflicts = {}
for family, (prefix, pattern) in patterns.items():
    groups = collections.defaultdict(list)
    for jar in jars:
        if jar.startswith(prefix):
            match = pattern.match(jar)
            if match:
                groups[match.group(1)].append(jar)
    duplicate_groups = {
        base: sorted(values) for base, values in groups.items() if len(values) > 1
    }
    if duplicate_groups:
        conflicts[family] = duplicate_groups

print(f"WAR integrity: {len(jars)} JARs; WEB-INF/web.xml present")
if conflicts:
    print("WAR integrity check failed: conflicting versioned libraries:")
    for family, values in conflicts.items():
        print(f"  {family}: {values}")
    raise SystemExit(1)
print("WAR integrity: no conflicting GeoNetwork, GeoTools, or Log4j versions")
PY
}

if [[ "${BUILD_WAR}" == true ]]; then
  (
    cd "${REPO_DIR}"
    # Upstream schema modules depend on each other's test JARs. Force their
    # creation for clean builds; incremental builds should reuse existing JARs.
    mvn_args=(-DskipTests -Penv-prod,war -pl web -am)
    if [[ "${CLEAN_WAR}" == true ]]; then
      mvn_args+=(-Dmaven.jar.forceCreation=true)
      mvn "${mvn_args[@]}" clean package
    else
      mvn "${mvn_args[@]}" package
    fi
  )

  if ! verify_war_integrity; then
    if [[ "${CLEAN_WAR}" == true ]]; then
      exit 1
    fi
    echo "Incremental WAR contains stale/conflicting libraries; retrying once with --clean-war." >&2
    (
      cd "${REPO_DIR}"
      mvn -DskipTests -Dmaven.jar.forceCreation=true -Penv-prod,war -pl web -am clean package
    )
    verify_war_integrity
  fi
fi

if [[ ! -f "${WAR_SOURCE}" ]]; then
  echo "Missing ${WAR_SOURCE}. Run this script with --build-war or build the WAR first." >&2
  exit 1
fi

if [[ "${BUILD_WAR}" != true ]]; then
  verify_war_integrity
fi

install -D -m 0644 "${WAR_SOURCE}" "${WAR_TARGET}"

mkdir -p \
  "${DEPLOY_DIR}/runtime/webapp/WEB-INF/classes" \
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
# Keep the record UI overrides available independently of the WAR build.
for path in \
  views/default/templates/izrk-facet-cards.html \
  views/default/templates/recordView/recordView.html \
  views/default/templates/recordView/title.html \
  views/default/templates/recordView/technical.html \
  views/default/templates/recordView/metadata.html \
  views/default/templates/recordView/share.html \
  views/default/templates/recordView/footer.html \
  views/default/templates/recordView/contact.html \
  views/default/templates/recordView/contacts.html \
  views/default/templates/recordView/metadatacontact.html \
  views/default/templates/recordView/processsteps.html \
  views/default/templates/recordView/type-dataset.html \
  views/default/templates/recordView/type-service.html \
  views/default/templates/recordView/type-series.html \
  components/search/mdview/mdviewDirective.js \
  components/search/mdview/partials/contact.html \
  components/search/mdview/partials/individual.html \
  components/metadataactions/partials/citation.html; do
  install -D -m 0644 \
    "${REPO_DIR}/web-ui/src/main/resources/catalog/${path}" \
    "${DEPLOY_DIR}/runtime/webapp/catalog/${path}"
done

# Remove the obsolete record-map implementation from any previously packaged overlay.
for path in \
  components/izrk/ExtentMap.js \
  lib/leaflet/LICENSE \
  lib/leaflet/leaflet.css \
  lib/leaflet/leaflet.js \
  lib/leaflet/images/layers.png \
  lib/leaflet/images/layers-2x.png \
  lib/leaflet/images/marker-icon.png \
  lib/leaflet/images/marker-icon-2x.png \
  lib/leaflet/images/marker-shadow.png; do
  rm -f "${DEPLOY_DIR}/runtime/webapp/catalog/${path}"
done

install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/catalog/views/default/module.js" \
  "${DEPLOY_DIR}/runtime/webapp/catalog/views/default/module.js"
install -D -m 0644 \
  "${REPO_DIR}/web-ui/src/main/resources/WEB-INF/classes/web-ui-wro-sources.xml" \
  "${DEPLOY_DIR}/runtime/webapp/WEB-INF/classes/web-ui-wro-sources.xml"
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

python3 "${SCRIPT_DIR}/package-standalone-footer.py" \
  "${REPO_DIR}" "${DEPLOY_DIR}/runtime/webapp"

python3 "${SCRIPT_DIR}/package-imageio.py"

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
