# LensCloud Platform MCPs

## Recommended Tooling

- Kubernetes MCP
  - inspect operator CRDs and runtime state
  - use only server-side restricted credentials for mutations
- GitHub tooling
  - issues, PRs, repo handoff, and publishing
- Edge/ingress inspection for shared wildcard readiness
  - inspect route, TLS, and ingress health without DNS-provider mutation
- Optional Frappe runtime inspector
  - bench, site, and app state visibility
- Optional spec-reader MCP
  - exposes repo docs and requirements as authoritative handoff context

MCP access does not replace the application credential contract. LensCloud
backend apply must use the restricted kubeconfig reference documented by
`lenscloud-infra/docs/platform-restricted-access-contract.md`.
