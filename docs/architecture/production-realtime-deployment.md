# Production realtime deployment

## Required ownership boundary

LensCloud uses Frappe's standard Socket.IO namespace and protected document
rooms. LensCloud owns its Vue client and exact-document subscription. Frappe
Docker owns the nginx-to-Socket.IO proxy, and Frappe owns namespace
authentication, room permissions, Redis publication, and room delivery.

Do not add a second LensCloud publisher for normal `Document.save()` calls.
Frappe v16 already publishes `doc_update` after commit.

## LensCloud client requirement

`app.use(FrappeUI)` creates a Socket.IO client unless explicitly disabled.
LensCloud also has an application-owned client for consistent dev and
production URL handling. The plugin must therefore be installed as:

```js
app.use(FrappeUI, { socketio: false })
```

There must be exactly one initial Engine.IO handshake per page.

## LensDocker image requirement

The `lenscloud-build` branch of `lmnaslimited/frappe_docker` currently carries
an obsolete `resources/core/nginx/nginx-template.conf` containing:

```nginx
proxy_set_header Origin $scheme://$http_host;
```

Behind Traefik, `$scheme` is `http` because TLS has already terminated. Frappe
Socket.IO uses Origin for its internal authenticated `get_user_info` and
`has_permission` callbacks. A transport and namespace can connect while a
Website User fails to join a protected document room.

Port the following forwarded-protocol map and `/socket.io` headers into the
existing LensDocker template:

```nginx
map $http_x_forwarded_proto $proxy_x_forwarded_proto {
	default $scheme;
	https https;
}

location /socket.io {
	proxy_http_version 1.1;
	proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	proxy_set_header X-Forwarded-Proto $proxy_x_forwarded_proto;
	proxy_set_header Upgrade $http_upgrade;
	proxy_set_header Connection "upgrade";
	proxy_set_header X-Frappe-Site-Name ${FRAPPE_SITE_NAME_HEADER};
	proxy_set_header Origin $proxy_x_forwarded_proto://${FRAPPE_SITE_NAME_HEADER};
	proxy_set_header Host $host;
	proxy_pass http://socketio-server;
}
```

Do not copy the whole current upstream template unless the image also copies
its `/etc/nginx/snippets/security_headers.conf` dependency. The minimal diff
above is self-contained for the existing LensDocker Containerfile.

The source file is baked into the image at
`/templates/nginx/frappe.conf.template`; `nginx-entrypoint.sh` renders it to
`/etc/nginx/conf.d/frappe.conf`. Fix the source template in the image build
context, not the generated container file.

The current Swarm router already terminates TLS and routes the frontend through
Traefik. No Raven Vite proxy or separate public Socket.IO router is required.
Raven's `vite.config.ts` proxy applies only to its development server.

## Build qualification

The LensDocker custom Containerfile should use the committed lockfile and run
the retained checks before producing assets:

```bash
npm ci
npm run test:realtime-config
npm run test:realtime
npm run build
```

Do not use an unpinned `npm install` for a release image.

## Runtime qualification

For an authenticated customer and readable Issue, prove all of the following:

1. Exactly one Engine.IO handshake is opened.
2. The namespace acknowledges `/qplatform.lmnaslens.com`.
3. The browser sends `doc_subscribe`, `Issue`, and the exact name.
4. The websocket service completes `frappe.realtime.has_permission` without
   `Can't check permissions`, `Unauthorized`, or redirect errors.
5. `redis-cli PUBSUB NUMSUB events` on `redis_queue` reports at least one
   subscriber.
6. A platform `Document.save()` produces one `doc_update` and the Vue resource
   reloads without polling.

The backend and websocket tasks must read the same `redis_queue` URL from the
shared `sites/common_site_config.json`. In Frappe v16.19, realtime publication
and subscription use `redis_queue`; merely defining a `redis-socketio` service
does not configure this path.
