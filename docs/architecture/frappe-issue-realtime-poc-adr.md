# Frappe Issue Realtime POC ADR

## Decision

LensCloud uses Frappe's existing realtime service. In development the Vue app
connects directly to `http://dev.localhost:9000/dev.localhost`; in production
it connects to the same origin at namespace `/dev.localhost`, leaving
`/socket.io` routing to the Frappe proxy/ingress.

The open Issue emits `doc_subscribe`, which Frappe permission-checks before
joining `doc:Issue/<name>`. `doc_update` is filtered by both doctype and name
before the resource reloads. Cleanup emits `doc_unsubscribe`; every socket
`connect` resubscribes because rooms are connection-local.

## Evidence and guide deviations

- Installed `frappe-ui` 0.1.278 selects Vite port 8080, proxies the standard
  Frappe paths with host-based site routing, derives output/base paths, and
  copies the generated Jinja page. LensCloud therefore removed port 5173,
  manual proxies (especially `/assets`), explicit base, and duplicate build
  output configuration.
- The local repo uses `package-lock.json`; `socket.io-client` was added with
  npm rather than creating a competing Yarn lockfile.
- The local DocType field is `summary`, not the guide's generic `subject`.
- Frappe v16 `Document.notify_update()` already publishes `doc_update` to the
  exact document room with `after_commit=True`; no custom publisher is added.
- `frappe.db.set_value()` bypasses `Document.notify_update()`. Use
  `Document.save()` plus commit, or `db_set(..., notify=True)` where justified.

## Local commands

```bash
cd /workspace/frappe-bench
bench use dev.localhost
bench start

cd /workspace/frappe-bench/apps/lenscloud/frontend
npm ci
npm run dev -- --host 0.0.0.0
```

Open `/lenscloud/customer/realtime-issue/<Issue name>` on
`http://dev.localhost:8080` using a customer allowed to read that Issue.

Production build:

```bash
cd /workspace/frappe-bench/apps/lenscloud/frontend
npm ci
npm run build
```

The build writes `lenscloud/public/frontend`, copies
`lenscloud/www/lenscloud.html`, and uses `/assets/lenscloud/frontend/`.

## Staging qualification checklist

- Route `/socket.io` to Frappe's Socket.IO service and preserve WebSocket
  `Upgrade` and `Connection` headers.
- Preserve `Host`, `Origin`, and (when used by the deployment) the correct
  `X-Frappe-Site-Name`; verify namespace and site resolve to the same tenant.
- Terminate TLS correctly and observe `wss://` from the browser.
- Point Python publishers and every Node Socket.IO instance at the same
  `redis_socketio`; test Redis publish/subscribe across instances.
- Keep `sid` Secure/HttpOnly/SameSite-appropriate on the LensCloud domain. Do
  not copy cross-domain cookies.
- Prove an allowed customer receives its Issue update and cannot subscribe to
  another customer's document room.
- Restart/rotate proxy and Socket.IO instances and prove reconnect plus room
  resubscription; repeat behind every horizontally scaled instance.
- Separate logs for transport/upgrade, origin/namespace, session
  authentication, permission, and Redis delivery failures.

## Rollback

Revert the POC branch commits, rebuild the frontend, and remove only the local
POC user, its two clearly named Issue fixtures, related User Permission, and
the local Issue Custom DocPerm rows created for testing. No Frappe core or CRM
files are changed.
