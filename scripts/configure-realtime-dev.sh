#!/usr/bin/env bash
set -euo pipefail

SITE_NAME="${1:-}"
SOCKETIO_PORT="${LENSCLOUD_SOCKETIO_PORT:-9000}"
BENCH_DIR="${LENSCLOUD_BENCH_DIR:-/workspace/frappe-bench}"

if [[ -z "${SITE_NAME}" || "${SITE_NAME}" == -* ]]; then
	echo "Usage: $0 <site-name>" >&2
	exit 2
fi
if [[ ! -d "${BENCH_DIR}/sites/${SITE_NAME}" ]]; then
	echo "Frappe site does not exist: ${BENCH_DIR}/sites/${SITE_NAME}" >&2
	exit 1
fi

cd "${BENCH_DIR}"
bench --site "${SITE_NAME}" set-config developer_mode 1
bench --site "${SITE_NAME}" set-config socketio_port "${SOCKETIO_PORT}"
bench use "${SITE_NAME}"
bench --site "${SITE_NAME}" clear-cache

if ! getent hosts "${SITE_NAME}" | awk '{print $1}' | grep -qx '127.0.0.1'; then
	echo "Adding ${SITE_NAME} to /etc/hosts for Socket.IO authentication"
	printf '127.0.0.1 %s\n' "${SITE_NAME}" | sudo tee -a /etc/hosts >/dev/null
fi

echo "Realtime configuration ready for ${SITE_NAME}."
echo "Run ./scripts/verify-realtime-dev.sh ${SITE_NAME} after bench and Vite are started."
