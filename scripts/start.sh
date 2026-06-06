#!/bin/bash
set -euo pipefail

BENCH_DIR="/workspace/frappe-bench"
NODE_VERSION="24.16.0"
export NVM_DIR="/home/frappe/.nvm"
export PATH="${BENCH_DIR}/env/bin:/home/frappe/.nvm/versions/node/v${NODE_VERSION}/bin:/home/frappe/.local/bin:${PATH}"

if [[ ! -x "${BENCH_DIR}/env/bin/python" ]]; then
  echo "Bench Python environment is missing; run scripts/init.sh first" >&2
  exit 1
fi

if pgrep -f "[b]ench start" >/dev/null 2>&1; then
  echo "Bench is already running"
  exit 0
fi

cd "$BENCH_DIR"
nohup bench start > /tmp/lenscloud-bench.log 2>&1 &

for _ in $(seq 1 30); do
  if curl --silent --show-error --fail --max-time 2 http://127.0.0.1:8000 >/dev/null 2>&1; then
    echo "Bench started on http://127.0.0.1:8000"
    exit 0
  fi
  sleep 1
done

echo "Bench did not become ready; see /tmp/lenscloud-bench.log" >&2
tail -n 80 /tmp/lenscloud-bench.log >&2 || true
exit 1
