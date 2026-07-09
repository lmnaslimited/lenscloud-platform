# Infra Handoff - CUA OAuth Local Dev Base URL Runner Contract - 2026-07-07

## Incident

`LC-E2E-20260707-003` CUA OAuth configure rejects LensCloud Platform local/dev issuer URL.

## Platform Context

LensCloud Platform is the CUA/OAuth provider. For local/dev acceptance the Platform issuer is:

```text
http://dev.localhost:8000
```

The target Site Social Login Key must be named:

```text
lenscloud
```

The target Site redirect URI is derived from the target Site access URL:

```text
<site.access_url>/api/method/frappe.integrations.oauth2_logins.custom/lenscloud
```

Customer `Open Site` opens the target Site URL. The target Site owns redirecting unauthenticated users to LensCloud Platform OAuth. `nectar` was only an example shape reference and must not be used as the Platform issuer.

## Live Failure

Platform reran corrected `oauth.configure` against the fresh CUA Site:

```text
Site: run-20260707-cua-oauth.cloud.lmnaslens.com
Command: oauth.configure
Action log: ORCH-2026-00239
Command ID: BCMD-2026-00239
Result: Failed
Code: INVALID_ARGUMENTS
Sanitized summary: oauth.configure base_url must be an https URL
```

Cleanup succeeded and removed:

```text
jobs/lenscloud-runtime-eu/bcmd-2026-00239-job
configmaps/lenscloud-runtime-eu/bcmd-2026-00239-request
pods/lenscloud-runtime-eu/bcmd-2026-00239-job-5kx2z
secrets/lenscloud-runtime-eu/bcmd-2026-00239-oauth-secret
```

No OAuth client secret, Kubernetes Secret value, kubeconfig, token, private key, password, pod log, or full environment dump was exposed.


## Operator Manual Validation

The operator manually logged in to target Site `run-20260707-cua-oauth` as Administrator and confirmed:

- a Social Login Key exists for the LensCloud flow;
- the configured base URL is still the old example `nectar` URL;
- the target Site client ID did not match the expected corresponding Platform OAuth Client entry for the corrected CUA contract.

This confirms Platform should not continue using the old HTTPS example URL simply to satisfy runner validation. The correct fix is to let local/dev use the actual Platform issuer or to provide a real HTTPS endpoint for the same Platform instance.

## Requested Infra Action

Please update the OAuth runner validation contract so Platform can complete local/dev CUA acceptance without using a wrong HTTPS issuer.

The source of truth for the issuer must be LensCloud **Platform Settings**:

- `oauth_base_url` provides the Platform OAuth issuer URL that the target Site Social Login Key should use.
- Platform must add an explicit boolean setting, proposed as `allow_local_oauth_http`, for local/dev only.
- Platform must pass that setting into the `oauth.configure` Bench Command request, proposed request arg: `allow_local_oauth_http: true`.
- The runner must accept plain HTTP only when both are true:
  - `allow_local_oauth_http` is true in the request; and
  - `base_url` is loopback/local-dev only, for example `http://localhost:<port>`, `http://*.localhost:<port>`, or `http://dev.localhost:<port>`.
- If the flag is missing or false, the runner must keep rejecting plain HTTP, including localhost HTTP.
- The runner must always reject non-localhost plain HTTP even when the flag is true.
- Productive/non-local URLs must remain HTTPS-only.

When the local/dev flag is accepted, the runner should configure the target Site Social Login Key from the Platform-provided values in the job request: provider `lenscloud`, provider name, client ID, mounted client secret, redirect URL, custom base URL, and `base_url` from Platform Settings. It must not fall back to the old `nectar` example or any hard-coded issuer.

Fallback only if Infra explicitly prefers it: provide and document an HTTPS Platform issuer URL for the current dev Platform instance that points to the same LensCloud Platform/CUA site, not an example or unrelated branded host.

After the fix, rerun Infra verification for `oauth.configure` with a local/dev Platform issuer and hand back:

- updated runner contract;
- positive evidence for `base_url=http://dev.localhost:8000` with `allow_local_oauth_http=true`, or the approved HTTPS Platform issuer;
- negative proof that `base_url=http://dev.localhost:8000` is rejected when `allow_local_oauth_http` is false or absent;
- negative proof that non-localhost plain HTTP is still rejected even when `allow_local_oauth_http=true`;
- proof that the target Site Social Login Key is configured from the Platform Settings URL and request payload, not a hard-coded/example issuer;
- cleanup proof for Job, ConfigMap, Pod, and Secret;
- Platform follow-up prompt.

## Platform Resume Point

After Infra handoff, Platform should rerun:

1. `oauth.status` provider `lenscloud`.
2. `configure_site_oauth` on `run-20260707-cua-oauth.cloud.lmnaslens.com`.
3. final `oauth.status` provider `lenscloud`.
4. Customer browser check: open Site URL, click `Login with LensCloud`, and confirm the customer reaches the Site without entering a Site-local password.

Do not delete the fresh Site; keep it for INF-023 user/access validation.
