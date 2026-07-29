# Realtime developer workflow

Configure any existing local site once:

```bash
./scripts/configure-realtime-dev.sh <site-name>
```

Start `bench start` and `npm --prefix frontend run dev`, then verify every
layer with a user that can read and update the selected Issue:

```bash
LENSCLOUD_REALTIME_PASSWORD='<password>' \
LENSCLOUD_REALTIME_ISSUE='<issue-name>' \
  ./scripts/verify-realtime-dev.sh <site-name>
```

`LENSCLOUD_REALTIME_USER` defaults to `Administrator`. Optional
`LENSCLOUD_PLATFORM_USER` and `LENSCLOUD_PLATFORM_PASSWORD` select a different
backend editor. The verifier checks the Vite contract, subscription lifecycle,
backend boot data, ports 8000/8080/9000, and three authenticated
save-to-browser deliveries.

To verify built assets:

```bash
npm --prefix frontend run build
LENSCLOUD_FRONTEND_MODE=build \
LENSCLOUD_REALTIME_PASSWORD='<password>' \
LENSCLOUD_REALTIME_ISSUE='<issue-name>' \
  ./scripts/verify-realtime-dev.sh <site-name>
```
