# Infra Handoff: Real Bench Runner Site Config Path Gap - 2026-06-29

> Status: Superseded by Infra revision `328846b`. Platform retried with runner image `sha256:3c322afc631b7db49759059c6706a3f42668cfbf5017ee66b3f4c26d9235c49e`; `maintenance_mode.status` passed in `ORCH-2026-00159` and cleanup was verified. See `docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md`.

## Context

Platform completed the real Free Plan public Prod path against the live EU cluster after API reachability was restored.

Evidence:

```text
apps/lenscloud/docs/evidence/bench-command/bench-command-real-site-runner-evidence-20260629.md
```

Key Platform action logs:

```text
ORCH-2026-00139 FrappeBench accepted
ORCH-2026-00140 FrappeBench Ready
ORCH-2026-00141 Free Plan Site request
ORCH-2026-00142 FrappeSite accepted
ORCH-2026-00155 Site Ready, HTTPS 200, static asset 200
ORCH-2026-00156 bench_test.status Succeeded, cleanup verified
ORCH-2026-00157 maintenance_mode.status Failed: TARGET_NOT_FOUND / site_config.json was not found, cleanup verified
ORCH-2026-00158 backup.create Unsupported / COMMAND_UNSUPPORTED
```

The real Bench sites PVC exists and is Bound:

```text
PVC: lenscloud-runtime-eu/run-20260629-free-prod-bench-sites
phase: Bound
storageClassName: local-path
requested: 3Gi
```

Platform currently mounts that PVC into the Bench Command runner Job at:

```text
/home/frappe/frappe-bench/sites
```

The runner searched for:

```text
/home/frappe/frappe-bench/sites/run-20260629-free-prod-site.cloud.lmnaslens.com/site_config.json
```

and returned:

```text
TARGET_NOT_FOUND: site_config.json was not found
```

No Secrets, pod logs, DB passwords, kubeconfig material, private keys, or file contents were exposed.

## Prompt For Infra Agent

Work inside `lenscloud-infra`.

Start from revision `f3d8057` or newer. Read:

1. `docs/infra-workitems.md`
2. `docs/platform-bench-command-handoff.md`
3. `docs/bench-command-production-runner-evidence-20260627.md`
4. the Platform evidence summary above

Update the canonical Infra backlog first with a dated workitem for the real Bench runner site path/mount contract gap.

Goal:

Fix or document the production Bench Command runner contract so `maintenance_mode.status` can read the real Frappe Operator-created Site `site_config.json` for a Platform-managed Bench/Site.

Investigate safely:

- the real FrappeBench sites PVC layout;
- whether the runner should mount a different PVC, subPath, or path;
- whether the Frappe Operator stores the Site under a different directory name;
- whether an init/sync step is required before the runner can see `site_config.json`;
- whether Platform needs a different PVC naming contract than `<bench operator_resource_name>-sites`.

Do not expose:

- Kubernetes Secret values;
- DB passwords;
- pod logs;
- kubeconfig contents;
- private keys;
- raw `site_config.json` contents;
- full environment dumps.

Allowed evidence:

- sanitized path existence checks;
- file/directory names if they contain no secrets;
- PVC names and phases;
- runner termination summaries;
- action status and cleanup proof.

Required return to Platform:

- Infra commit hash;
- updated `docs/infra-workitems.md`;
- updated `docs/platform-bench-command-handoff.md` if the mount/path contract changes;
- dated evidence document;
- exact Platform Job volume/mount contract to use;
- live positive proof for `maintenance_mode.status` against a real Frappe Operator-created Site;
- cleanup proof;
- a Platform handoff prompt describing the required code/config changes, if any.
