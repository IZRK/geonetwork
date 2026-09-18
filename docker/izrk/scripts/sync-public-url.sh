#!/usr/bin/env bash
set -euo pipefail

PUBLIC_URL="${GEONETWORK_PUBLIC_URL:-}"
if [[ -z "${PUBLIC_URL}" ]]; then
  echo "GEONETWORK_PUBLIC_URL is not set; keeping the GeoNetwork server URL unchanged."
  exit 0
fi

if [[ ! "${PUBLIC_URL}" =~ ^(https?)://(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9._-]+)(:([0-9]{1,5}))?$ ]]; then
  echo "Invalid GEONETWORK_PUBLIC_URL: ${PUBLIC_URL}" >&2
  echo "Use an origin without a path, for example http://172.16.1.31:8080" >&2
  exit 1
fi

PROTOCOL="${BASH_REMATCH[1]}"
HOST="${BASH_REMATCH[2]}"
PORT="${BASH_REMATCH[4]:-}"
HOST="${HOST#[}"
HOST="${HOST%]}"

if [[ -z "${PORT}" ]]; then
  if [[ "${PROTOCOL}" == "https" ]]; then
    PORT=443
  else
    PORT=80
  fi
fi

WEBAPP_ROOT="${GEONETWORK_WEBAPP_ROOT:-/usr/local/tomcat/webapps/ROOT}"
DB_BASE="${GEONETWORK_DB_BASE:-/root/gn}"
DB_FILE="${DB_BASE}.mv.db"
H2_JAR="${H2_JAR:-}"
DB_USER="${GEONETWORK_DB_USER:-www-data}"
DB_PASSWORD="${GEONETWORK_DB_PASSWORD:-www-data}"

# A new H2 database does not exist until GeoNetwork has initialized it. The
# first startup can continue; a subsequent restart will apply this setting.
if [[ ! -f "${DB_FILE}" ]]; then
  echo "GeoNetwork database not found at ${DB_FILE}; public URL sync deferred."
  exit 0
fi

if [[ -z "${H2_JAR}" ]]; then
  H2_JAR="$(find "${WEBAPP_ROOT}/WEB-INF/lib" -maxdepth 1 -type f -name 'h2-*.jar' | sort -V | tail -n 1)"
fi

if [[ ! -f "${H2_JAR}" ]]; then
  echo "H2 jar not found; cannot update ${DB_FILE}. Set H2_JAR to an H2 jar." >&2
  exit 1
fi

h2_shell() {
  java -Dfile.encoding=UTF-8 -cp "${H2_JAR}" org.h2.tools.Shell \
    -url "jdbc:h2:file:${DB_BASE};IFEXISTS=TRUE;NON_KEYWORDS=VALUE" \
    -user "${DB_USER}" \
    -password "${DB_PASSWORD}" \
    "$@"
}

echo "Synchronizing GeoNetwork public URL to ${PUBLIC_URL}"
h2_shell -sql "SELECT NAME, \"VALUE\" FROM SETTINGS WHERE NAME IN ('system/server/host', 'system/server/protocol', 'system/server/port') ORDER BY NAME"

read -r -d '' UPDATE_SQL <<SQL || true
SET AUTOCOMMIT FALSE;
UPDATE SETTINGS SET "VALUE"='${HOST}' WHERE NAME='system/server/host';
UPDATE SETTINGS SET "VALUE"='${PROTOCOL}' WHERE NAME='system/server/protocol';
UPDATE SETTINGS SET "VALUE"='${PORT}' WHERE NAME='system/server/port';

UPDATE METADATA SET DATA=REPLACE(DATA, 'http://localhost:8080/geonetwork/srv/', '${PUBLIC_URL}/srv/')
WHERE DATA LIKE '%http://localhost:8080/geonetwork/srv/%';
UPDATE METADATA SET DATA=REPLACE(DATA, 'https://localhost:8080/geonetwork/srv/', '${PUBLIC_URL}/srv/')
WHERE DATA LIKE '%https://localhost:8080/geonetwork/srv/%';
UPDATE METADATA SET DATA=REPLACE(DATA, 'http://localhost:8080/srv/', '${PUBLIC_URL}/srv/')
WHERE DATA LIKE '%http://localhost:8080/srv/%';
UPDATE METADATA SET DATA=REPLACE(DATA, 'https://localhost:8080/srv/', '${PUBLIC_URL}/srv/')
WHERE DATA LIKE '%https://localhost:8080/srv/%';
UPDATE METADATA SET DATA=REPLACE(DATA, 'http://127.0.0.1:8080/srv/', '${PUBLIC_URL}/srv/')
WHERE DATA LIKE '%http://127.0.0.1:8080/srv/%';
UPDATE METADATA SET DATA=REPLACE(DATA, 'https://127.0.0.1:8080/srv/', '${PUBLIC_URL}/srv/')
WHERE DATA LIKE '%https://127.0.0.1:8080/srv/%';
UPDATE METADATA SET DATA=REPLACE(DATA, 'http://localhost/srv/', '${PUBLIC_URL}/srv/')
WHERE DATA LIKE '%http://localhost/srv/%';
UPDATE METADATA SET DATA=REPLACE(DATA, 'https://localhost/srv/', '${PUBLIC_URL}/srv/')
WHERE DATA LIKE '%https://localhost/srv/%';

-- Repair the misspelled production origin, including embedded attachments.
-- Do not change unrelated links or email addresses.
UPDATE METADATA SET DATA=REPLACE(DATA, 'https://metadata.izrk.zrcsazu.si/', '${PUBLIC_URL}/')
WHERE DATA LIKE '%https://metadata.izrk.zrcsazu.si/%';
UPDATE METADATA SET DATA=REPLACE(DATA, 'http://metadata.izrk.zrcsazu.si/', '${PUBLIC_URL}/')
WHERE DATA LIKE '%http://metadata.izrk.zrcsazu.si/%';

COMMIT;
SQL

# Shell prints SQL errors but can still exit successfully. RunScript fails the
# startup on any SQL error instead of continuing with partially updated data.
sql_file="$(mktemp)"
trap 'rm -f "${sql_file}"' EXIT
printf '%s\n' "${UPDATE_SQL}" > "${sql_file}"
java -Dfile.encoding=UTF-8 -cp "${H2_JAR}" org.h2.tools.RunScript \
  -url "jdbc:h2:file:${DB_BASE};IFEXISTS=TRUE;NON_KEYWORDS=VALUE" \
  -user "${DB_USER}" -password "${DB_PASSWORD}" -script "${sql_file}"
h2_shell -sql "SELECT NAME, \"VALUE\" FROM SETTINGS WHERE NAME IN ('system/server/host', 'system/server/protocol', 'system/server/port') ORDER BY NAME"
echo "GeoNetwork public URL synchronization complete."
