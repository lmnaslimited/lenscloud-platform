# LensCloud UI Contract

## Product Boundaries

- Native Frappe authentication and permissions remain authoritative.
- Platform users manage Customers, Clusters, Database Servers, Release Groups,
  Releases, Benches, Sites, orchestration actions, and runtime status.
- Customers manage their account and request or inspect their own Sites.
- Customers never select Database Server records or see Kubernetes namespaces,
  CR names, kubeconfig references, credentials, secret references, or other
  customers sharing infrastructure.

## Workspace

- Left navigation carries scope and product navigation.
- Main workspace carries lists, workflows, timelines, and primary actions.
- Right inspector carries summary, editable fields, status, related records,
  external context, and history.
- The assistant drawer is optional and secondary.
- Editable fields and read-only runtime status must remain visually distinct.

## Provisioning Experience

- Bench, Database Server, and Site actions show real backend progress and errors.
- Standard Site hostnames are `{subdomain}.cloud.lmnaslens.com`.
- Site provisioning never shows Route53, GoDaddy, ACME, or per-Site certificate
  steps.
- Customers see friendly placement and isolation descriptions, not operator
  implementation details.
- Public, Private Shared, and Private are LensCloud placement policies. The UI
  must not describe the Frappe Operator's `mode: shared` as a privacy level.

## Visual Restraint

- Use the existing LensCloud palette, spacing, borders, and typography.
- Avoid marketing-style composition, ornamental gradients, decorative blobs,
  excessive cards, and oversized empty-state artwork.
- Prefer clear tables, lists, status strips, tabs, dialogs, and concise forms.
- Add bespoke CSS only when Frappe UI and existing LensCloud patterns cannot
  express the required behavior.
