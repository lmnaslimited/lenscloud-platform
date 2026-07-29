#!/usr/bin/env bash
set -euo pipefail

SITE_NAME="${1:-}"
BENCH_DIR="${LENSCLOUD_BENCH_DIR:-/workspace/frappe-bench}"
APP_DIR="${BENCH_DIR}/apps/lenscloud"
WEB_PORT="${LENSCLOUD_WEB_PORT:-8000}"
VITE_PORT="${LENSCLOUD_VITE_PORT:-8080}"
SOCKETIO_PORT="${LENSCLOUD_SOCKETIO_PORT:-9000}"
FRONTEND_MODE="${LENSCLOUD_FRONTEND_MODE:-dev}"

if [[ -z "${SITE_NAME}" || "${SITE_NAME}" == -* ]]; then
	echo "Usage: $0 <site-name>" >&2
	exit 2
fi

check_url() {
	local label="$1" port="$2" path="$3"
	curl --fail --silent --show-error \
		--resolve "${SITE_NAME}:${port}:127.0.0.1" \
		"http://${SITE_NAME}:${port}${path}" >/dev/null
	echo "PASS: ${label}"
}

cd "${APP_DIR}"
npm --prefix frontend run test:realtime-container -- \
	"${SITE_NAME}" "${WEB_PORT}" "${VITE_PORT}" "${SOCKETIO_PORT}"
npm --prefix frontend run test:realtime-config
npm --prefix frontend run test:realtime
bench --site "${SITE_NAME}" run-tests \
	--app lenscloud --module lenscloud.tests.test_realtime_boot
check_url "Frappe web" "${WEB_PORT}" "/api/method/ping"
check_url "Socket.IO polling handshake" "${SOCKETIO_PORT}" \
	"/socket.io/?EIO=4&transport=polling"

export LENSCLOUD_SITE_ORIGIN="http://${SITE_NAME}:${WEB_PORT}"
if [[ "${FRONTEND_MODE}" == "dev" ]]; then
	check_url "Vite client" "${VITE_PORT}" "/@vite/client"
	export LENSCLOUD_FRONTEND_ORIGIN="http://${SITE_NAME}:${VITE_PORT}"
else
	check_url "built frontend" "${WEB_PORT}" "/lenscloud"
	export LENSCLOUD_FRONTEND_ORIGIN="http://${SITE_NAME}:${WEB_PORT}"
fi

if [[ -z "${LENSCLOUD_REALTIME_PASSWORD:-}" || -z "${LENSCLOUD_REALTIME_ISSUE:-}" ]]; then
	echo "Set LENSCLOUD_REALTIME_PASSWORD and LENSCLOUD_REALTIME_ISSUE for the browser proof." >&2
	echo "LENSCLOUD_REALTIME_USER defaults to Administrator." >&2
	exit 1
fi
export LENSCLOUD_REALTIME_USER="${LENSCLOUD_REALTIME_USER:-Administrator}"
npm --prefix frontend run test:realtime-auth
echo "PASS: all realtime checks succeeded for ${SITE_NAME} (${FRONTEND_MODE})"
