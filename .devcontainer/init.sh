#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE:-/workspace/lenscloud}"
BENCH_DIR="/home/frappe/frappe-bench"
SITE_NAME="development.localhost"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-admin}"
DB_NAME="${DB_NAME:-frappe}"
DB_USER="${DB_USER:-frappe}"
DB_PASSWORD="${DB_PASSWORD:-frappe}"

mkdir -p "${WORKSPACE_DIR}"

wait_for_port() {
  local host="$1"
  local port="$2"
  local retries="${3:-60}"
  local delay="${4:-2}"

  for _ in $(seq 1 "${retries}"); do
    if python3 - "$host" "$port" <<'PY' >/dev/null 2>&1; then
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(1)
try:
    sock.connect((host, port))
finally:
    sock.close()
PY
      return 0
    fi
    sleep "${delay}"
  done

  echo "Timed out waiting for ${host}:${port}" >&2
  return 1
}

if ! command -v bench >/dev/null 2>&1; then
  echo "bench is not available in the workspace image" >&2
  exit 1
fi

wait_for_port mariadb 3306 60 2

if [ ! -d "${BENCH_DIR}" ]; then
  echo "Initializing Frappe bench at ${BENCH_DIR}"
  bench init --skip-redis-config-generation --frappe-branch version-15 "${BENCH_DIR}"
fi

cd "${BENCH_DIR}"

cat > sites/common_site_config.json <<EOF
{
  "db_host": "mariadb",
  "db_port": 3306,
  "redis_cache": "redis-cache:6379",
  "redis_queue": "redis-queue:6379",
  "redis_socketio": "redis-socketio:6379",
  "db_root_password": "${DB_ROOT_PASSWORD}"
}
EOF

if [ ! -d "sites/${SITE_NAME}" ]; then
  echo "Creating ${SITE_NAME}"
  bench new-site "${SITE_NAME}" \
    --db-host mariadb \
    --db-port 3306 \
    --db-root-password "${DB_ROOT_PASSWORD}" \
    --admin-password admin \
    --no-mariadb-socket
fi

if [ ! -d "apps/lenscloud" ]; then
  echo "Creating placeholder lenscloud app scaffold"
  bench new-app lenscloud --no-git
fi

bench --site "${SITE_NAME}" install-app lenscloud || true
bench --site "${SITE_NAME}" set-config developer_mode 1 || true

echo "LensCloud devcontainer is ready."
echo "Open http://localhost:8000 after bench services are started by the devcontainer."
