#!/usr/bin/env bash
set -euo pipefail

WAR_PATH="/usr/local/tomcat/webapps/ROOT.war"
WEBAPP_ROOT="/usr/local/tomcat/webapps/ROOT"
DATA_DIR="${geonetwork_dir:-/var/lib/geonetwork_data}"
HTML_CACHE_DIR="${DATA_DIR}/data/resources/htmlcache"
WEBAPP_HASH_MARKER="${HTML_CACHE_DIR}/.izrk-root-webapp.sha256"
SCHEMA_PLUGIN_DIR="${DATA_DIR}/config/schema_plugins"
IZRK_SCHEMA_PLUGIN="eml-gbif"
IZRK_SCHEMA_PLUGIN_SRC="/opt/izrk/schema_plugins/${IZRK_SCHEMA_PLUGIN}"

/usr/local/bin/izrk-sync-public-url.sh

sync_izrk_schema_plugin() {
  local tmp_dir

  if [[ -d "${IZRK_SCHEMA_PLUGIN_SRC}" ]]; then
    mkdir -p "${SCHEMA_PLUGIN_DIR}/${IZRK_SCHEMA_PLUGIN}"
    cp -a "${IZRK_SCHEMA_PLUGIN_SRC}/." "${SCHEMA_PLUGIN_DIR}/${IZRK_SCHEMA_PLUGIN}/"
    return
  fi

  tmp_dir="$(mktemp -d)"
  (
    cd "${tmp_dir}"
    if [[ -f "${WAR_PATH}" ]]; then
      jar xf "${WAR_PATH}" "WEB-INF/data/config/schema_plugins/${IZRK_SCHEMA_PLUGIN}"
    elif [[ -d "${WEBAPP_ROOT}/WEB-INF/data/config/schema_plugins/${IZRK_SCHEMA_PLUGIN}" ]]; then
      mkdir -p "WEB-INF/data/config/schema_plugins"
      cp -a "${WEBAPP_ROOT}/WEB-INF/data/config/schema_plugins/${IZRK_SCHEMA_PLUGIN}" \
        "WEB-INF/data/config/schema_plugins/${IZRK_SCHEMA_PLUGIN}"
    fi
  )

  if [[ -d "${tmp_dir}/WEB-INF/data/config/schema_plugins/${IZRK_SCHEMA_PLUGIN}" ]]; then
    mkdir -p "${SCHEMA_PLUGIN_DIR}/${IZRK_SCHEMA_PLUGIN}"
    cp -a "${tmp_dir}/WEB-INF/data/config/schema_plugins/${IZRK_SCHEMA_PLUGIN}/." \
      "${SCHEMA_PLUGIN_DIR}/${IZRK_SCHEMA_PLUGIN}/"
  fi

  rm -rf "${tmp_dir}"
}

webapp_hash() {
  {
    printf '%s\n' "${GEONETWORK_PUBLIC_URL:-}"
    if [[ -f /opt/izrk/deploy-manifest.sha256 ]]; then
      sha256sum /opt/izrk/deploy-manifest.sha256
    fi
    if [[ -f "${WAR_PATH}" ]]; then
      sha256sum "${WAR_PATH}"
    fi

    for path in \
      "${WEBAPP_ROOT}/catalog/views/default/templates/home.html" \
      "${WEBAPP_ROOT}/catalog/views/default/templates/index.html" \
      "${WEBAPP_ROOT}/catalog/views/default/templates/footer.html" \
      "${WEBAPP_ROOT}/catalog/views/default/templates/recordView/recordView.html" \
      "${WEBAPP_ROOT}/catalog/js/CatController.js" \
      "${WEBAPP_ROOT}/catalog/style/srv_custom_style.less" \
      "${IZRK_SCHEMA_PLUGIN_SRC}"; do
      if [[ -f "${path}" ]]; then
        sha256sum "${path}"
      elif [[ -d "${path}" ]]; then
        find "${path}" -type f -print0 | sort -z | xargs -0 sha256sum
      fi
    done
  } | sha256sum | awk '{print $1}'
}

refresh_bundled_config() {
  local relative_path target source backup_dir
  local bundled_data="${WEBAPP_ROOT}/WEB-INF/data"
  backup_dir="${DATA_DIR}/config-backups/$(date -u +%Y%m%dT%H%M%S)-$$"

  # GeoNetwork initially copies these files into the persistent data directory,
  # but does not replace them on an application upgrade. They are application
  # code/configuration; records, uploads, custom plugins and other formatters
  # stay in their existing directories. Archive each previous bundled copy.
  for relative_path in \
    config/index \
    config/schema_plugins/csw-record \
    config/schema_plugins/dublin-core \
    config/schema_plugins/iso19110 \
    config/schema_plugins/iso19115-3.2018 \
    config/schema_plugins/iso19139 \
    data/formatter/xslt; do
    source="${bundled_data}/${relative_path}"
    target="${DATA_DIR}/${relative_path}"
    [[ -d "${source}" ]] || continue
    if [[ -d "${target}" ]]; then
      mkdir -p "${backup_dir}/$(dirname "${relative_path}")"
      mv "${target}" "${backup_dir}/${relative_path}"
    fi
    mkdir -p "$(dirname "${target}")"
    cp -a "${source}" "${target}"
  done
}

if [[ -f "${WAR_PATH}" || -d "${WEBAPP_ROOT}" ]]; then
  sync_izrk_schema_plugin

  mkdir -p "${HTML_CACHE_DIR}"
  current_hash="$(webapp_hash)"
  previous_hash="$(cat "${WEBAPP_HASH_MARKER}" 2>/dev/null || true)"

  if [[ "${current_hash}" != "${previous_hash}" ]]; then
    refresh_bundled_config
    # Formatter HTML embeds the public origin and indexed record information.
    # Keep the old cache for recovery, but never serve it after a deploy change.
    if [[ -d "${HTML_CACHE_DIR}/formatter-cache" ]]; then
      cache_backup="${DATA_DIR}/data/resources/htmlcache-backups/$(date -u +%Y%m%dT%H%M%S)-$$"
      mkdir -p "${cache_backup}"
      mv "${HTML_CACHE_DIR}/formatter-cache" "${cache_backup}/formatter-cache"
    fi
    rm -f "${HTML_CACHE_DIR}"/wro4j-cache* "${HTML_CACHE_DIR}"/wro4j*.db
    printf '%s\n' "${current_hash}" > "${WEBAPP_HASH_MARKER}"
  fi
fi

exec catalina.sh run
