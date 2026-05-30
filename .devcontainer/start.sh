#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="/home/frappe/frappe-bench"
SITE_NAME="development.localhost"

if ! command -v bench >/dev/null 2>&1; then
  echo "bench is not available in the workspace image" >&2
  exit 1
fi

if [ ! -d "${BENCH_DIR}" ]; then
  echo "Bench directory missing at ${BENCH_DIR}; run init first." >&2
  exit 0
fi

cd "${BENCH_DIR}"

if pgrep -f "bench start" >/dev/null 2>&1; then
  echo "bench start is already running."
  exit 0
fi

echo "Starting Frappe services for ${SITE_NAME}"
nohup bench start >/tmp/lenscloud-bench.log 2>&1 &
