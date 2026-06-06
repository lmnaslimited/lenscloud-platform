#!/bin/bash
set -euo pipefail

BENCH_DIR="/workspace/frappe-bench"
SITE_NAME="dev.localhost"
PYTHON_VERSION="3.14"
NODE_VERSION="24.16.0"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-123}"
export NVM_DIR="/home/frappe/.nvm"
export PATH="/home/frappe/.nvm/versions/node/v${NODE_VERSION}/bin:/home/frappe/.local/bin:${PATH}"

# These directories are initialized as frappe-owned before VS Code attaches.
mkdir -p \
  /home/frappe/.vscode-server \
  /home/frappe/.cache \
  /home/frappe/.local

source "$NVM_DIR/nvm.sh"
nvm use "$NODE_VERSION"

PYTHON_BIN="$(uv python find "$PYTHON_VERSION")"

if [[ -d "$BENCH_DIR/apps/frappe" ]]; then
  if [[ ! -x "$BENCH_DIR/env/bin/python" ]] \
    || ! "$BENCH_DIR/env/bin/python" --version 2>&1 | grep -q "Python ${PYTHON_VERSION}" \
    || ! "$BENCH_DIR/env/bin/python" -c "import frappe" >/dev/null 2>&1; then
    echo "Repairing the Frappe bench Python ${PYTHON_VERSION} environment"
    uv venv --clear --seed --python "$PYTHON_BIN" "$BENCH_DIR/env"
    cd "$BENCH_DIR"
    bench setup requirements
  fi

  echo "Bench already exists and its runtime is ready"
  exit 0
fi

# Ensure bench dir exists. The workspace is a host bind mount and must not be
# recursively chowned from inside the container.
mkdir -p "$BENCH_DIR"

cd /workspace

bench init \
  --ignore-exist \
  --skip-redis-config-generation \
  --frappe-branch version-16 \
  --python "$PYTHON_BIN" \
  frappe-bench

cd "$BENCH_DIR"

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis-cache:6379
bench set-redis-queue-host redis://redis-queue:6379
bench set-redis-socketio-host redis://redis-socketio:6379

# Remove redis from Procfile because redis is external container
sed -i '/redis/d' ./Procfile || true

bench new-site "$SITE_NAME" \
  --db-host mariadb \
  --mariadb-root-username root \
  --mariadb-root-password "$DB_ROOT_PASSWORD" \
  --admin-password admin \
  --mariadb-user-host-login-scope='%'

bench --site "$SITE_NAME" set-config developer_mode 1
bench --site "$SITE_NAME" clear-cache
bench use "$SITE_NAME"

echo "Frappe bench setup completed."
