# LensCloud Frappe Realtime Issue POC Implementation Guide

This guide reflects the locally validated Frappe v16 architecture. The site is
`dev.localhost`; Frappe web is 8000, the installed `frappe-ui` Vite plugin
selects 8080, and Socket.IO is 9000.

Use `frappeProxy: true` as the sole owner of standard Frappe proxying. Do not
add manual `/api`, `/assets`, `/files`, `/private`, login, logout, or
`/socket.io` Vite rules. The plugin also derives the production output and
`/assets/lenscloud/frontend/` base and copies the Jinja-compatible page.

The backend boot context must supply a non-empty `site_name`, positive numeric
`socketio_port`, and CSRF token. Development fetches this read-only context
through Vite with GET so an authenticated session does not need a CSRF token
before retrieving its CSRF token.
The browser connects with its normal Frappe `sid` and `withCredentials: true`.
When the local page has an explicit port (8000 or 8080), it connects to
`http://dev.localhost:9000/dev.localhost`. A normal production URL has no
explicit port and uses the current origin plus namespace `/dev.localhost`,
relying on ingress `/socket.io` routing.

For an open Issue, emit `doc_subscribe`, `Issue`, and the exact name. Frappe
permission-checks the request before joining `doc:Issue/<name>`. Filter
`doc_update` by both doctype and name, reload the document resource, emit
`doc_unsubscribe` on unmount, and resubscribe on every connection.

`Document.save()` calls `Document.notify_update()`, which publishes after
commit. Do not add a duplicate publisher. A raw `frappe.db.set_value()` is not
the supported notification path.

Commands, deviations, rollback, and the staging ingress/security checklist are
recorded in [the implementation ADR](./frappe-issue-realtime-poc-adr.md).
