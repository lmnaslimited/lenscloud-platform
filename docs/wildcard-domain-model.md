# Wildcard Domain And TLS Model

## Purpose

LensCloud customer sites use one shared root domain:

```text
cloud.lmnaslens.com
```

Customer hostnames are created as:

```text
{subdomain}.cloud.lmnaslens.com
```

Normal customer Site provisioning does not create a DNS record or certificate. A preconfigured wildcard DNS record and wildcard TLS certificate cover all valid customer subdomains.

## Platform Contract

Platform Settings must define:

- root domain: `cloud.lmnaslens.com`
- domain strategy: `Wildcard`
- wildcard DNS readiness/status
- wildcard TLS readiness/status
- ingress/routing readiness/status

GoDaddy remains authoritative for `lmnaslens.com`. Infra owns the
`cloud.lmnaslens.com` apex/wildcard records and temporary ACME challenge
records. Provider details, API credentials, wildcard targets, certificate
issuer details, and TLS Secret names are infrastructure configuration.
LensCloud may display non-secret readiness summaries but must not own or expose
secret values.

No DNS provider API integration is required in LensCloud Platform for Phase 1.

## Site Provisioning

The normal customer and platform Site flow is:

1. Validate and reserve a unique subdomain.
2. Derive `{subdomain}.cloud.lmnaslens.com`.
3. Select Region, Cluster, Bench, and Database Server through placement policy.
4. Create LensCloud metadata.
5. Create/reconcile the Frappe Site and its database.
6. Create/reconcile ingress or routing configuration for the hostname.
7. Verify that the route is reachable through the shared wildcard edge.

Do not:

- create a per-Site DNS record
- call any DNS provider
- wait for DNS propagation
- request a per-Site certificate
- create a per-Site ACME challenge

## Site State

Existing Site DNS fields may remain temporarily for compatibility, but their meaning changes:

- `dns_status` represents shared wildcard DNS readiness or route readiness, not a per-Site DNS transaction.
- `dns_record_name` is not required for standard wildcard Sites.
- DNS Record documents are not created for standard customer subdomains.
- A future custom-domain feature may reuse DNS Record as a separate workflow.

Recommended Site lifecycle fields:

- hostname
- hostname reservation status
- route status
- TLS status inherited from the Cluster edge
- last route check
- last route error

Site must not be marked accessible merely because the wildcard exists. The platform must also confirm that Site provisioning and hostname routing are ready.

## Customer Experience

Customers provide only a company/site name or preferred subdomain. They see:

- final hostname
- Region
- Plan
- provisioning status
- route/access status

Customers do not see:

- DNS provider API details
- wildcard record configuration
- GoDaddy wildcard record readiness
- wildcard certificate renewal readiness
- certificate issuer configuration
- TLS Secret names
- ingress controller internals

## Multi-Region Rule

The wildcard removes per-Site DNS operations, but it does not by itself select EU vs US origin.

For the current EU-first implementation:

- `*.cloud.lmnaslens.com` targets the EU platform ingress endpoint.

Before US production onboarding, infrastructure must provide one of:

- a global load-balancing layer that routes hostnames to the correct regional origin
- a central ingress/gateway that forwards to the selected Cluster
- a revised regional domain strategy

LensCloud Region remains the placement source of truth. The edge-routing solution must honor that placement without reintroducing per-customer DNS records.

## Custom Domains

Customer-owned custom domains are out of scope for the standard wildcard flow. They will require a separate verification, DNS, routing, and certificate lifecycle when introduced.

Future DNS automation may be justified for:

- customer-owned custom domains
- automated ownership-verification records
- automatic regional/global traffic steering if the selected edge requires DNS changes
- disaster-recovery origin switching when a global load balancer is unavailable

These are separate future workflows and must not be implemented in Phase 1 customer onboarding.
