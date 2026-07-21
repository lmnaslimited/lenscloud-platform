# Expected Infra Return — Customer Site Creation App Installation Latency

Date: 2026-07-21
From: Infra
To: Platform
Status: Awaiting Infra

## Infra Commit Range

Pending.

## Operator Init Phase Timings

Pending for Site creation, database initialization, each app install, migrations, and Ready reconciliation.

## Optimization Delivered

Pending.

## Fresh Proof

Pending. Include FrappeSite creation timestamp, Ready transition, requested/installed/failed apps, image cache evidence, and warnings.

## Platform Return Actions

After Infra return, Platform will separately optimize command cleanup off the customer-critical path, rerun setup/OAuth timing on the retained Ready Site, and only request another fresh customer reset when the combined budget can plausibly remain below 300 seconds.
