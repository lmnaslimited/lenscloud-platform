# Stitch Customer Portal Design Prompt

Use this prompt with Stitch and attach current LensCloud customer and Platform screenshots as structural references.

> Redesign LensCloud as a responsive SaaS customer portal using Frappe UI and Frappe CRM visual conventions. Use the supplied current screens as structural references, but simplify them substantially. Design desktop and mobile screens for post-signup onboarding, Free Plan selection, Region and subdomain setup, provisioning progress, empty and ready dashboards, Sites, Account, and beta Plan enrollment. Customers must never see Kubernetes, namespaces, Benches, MariaDB, Secrets, CR names, or infrastructure sharing details. Use compact typography, restrained cards, clear status steps, one obvious primary action, accessible controls, Frappe color tokens, and no gradients or decorative marketing artwork. Also propose a compact Platform launch-readiness dashboard and collapsible grouped sidebar. Provide reusable component states for loading, empty, validation, provisioning, ready, failed, retry, and approval pending.

## Required Deliverables

- Desktop and mobile flows for signup completion, first Site creation, provisioning, ready, failed/retry, Sites, Account, and beta enrollment.
- A compact Platform launch-readiness dashboard and grouped navigation.
- Reusable Frappe UI component states and design tokens.
- An interaction note for every primary action, validation state, empty state, and recovery path.
- Accessibility annotations for focus order, keyboard use, contrast, and status text.

This is a design track. The canonical implementation backlog remains `docs/platform-workitems.md`.
