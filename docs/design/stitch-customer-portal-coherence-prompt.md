# Stitch Customer Portal Visual Coherence Prompt

Use this prompt with Stitch after attaching the current LensCloud customer portal screenshots and the existing non-legacy Stitch artifacts under `docs/design/stitch_lenscloud_designs/`. Legacy folders are reference-only for what exists today; do not use them as the target design language.

## Goal

Redesign the LensCloud customer portal as one coherent, premium Frappe-native product experience. The current implementation has useful functional pieces, but the screens do not yet feel like one product family. Treat every weak visual, unclear transition, cramped card, inconsistent button, or mobile dead end as a revenue leak.

The strongest current reference is the customer Subscription screen pattern: card-led primary content, a focused detail/inspector surface, restrained blue actions, compact status language, and customer-safe terminology. Use that spirit across the portal.

## Product Flow

Design the customer journey as a guided activity:

1. Dashboard as the launch home.
2. Choose a Plan.
3. Set up the first Site.
4. Review Subscription.
5. Confirm Free checkout or request access for paid/beta Plans.
6. Watch provisioning progress.
7. Open the ready Site.
8. Return later to Dashboard, Subscriptions, and Account.

Customers must never see or choose Kubernetes, namespaces, Benches, MariaDB, Database Servers, CR names, Secrets, kubeconfig, pod logs, action logs, or infrastructure sharing details. Use customer language: Plan, Subscription, Region, Site, workspace, setup, access, support, progress, and readiness.

## Required Screens

Provide desktop and mobile designs for:

- Dashboard with no Subscription.
- Dashboard with provisioning Subscription.
- Dashboard with ready Subscription.
- Plan browsing with customer-facing Public/Private choice, default Plan emphasis, entitlement-exhausted disabled state, request-access state, and hidden Enterprise/Four Tier behavior.
- Setup Site using active Region choices and Platform domain suffix.
- Review Subscription.
- Free checkout confirmation showing zero due today and no payment method required.
- Provisioning progress with normal, delayed, failed/retry, and ready states.
- Subscriptions list/detail using Landscape environment progression instead of a generic Sites list.
- Account and Access page placed in the bottom/profile navigation area, not as a primary service workflow.
- Mobile inspector/detail drawer pattern for Subscriptions, Account, and any other split-detail page.
- Customer sidebar/navigation with primary workflow items separated from bottom Account/profile items.

## Design System Requirements

Use the LensCloud Service Portal design contract from `docs/design/stitch_lenscloud_designs/lenscloud_service_portal/DESIGN.md`:

- Primary blue: `#1D4ED8`.
- Success green: `#10B981`.
- Light product background: `#F7F9FB` or equivalent token.
- White cards with subtle borders.
- Inter typography.
- 4px spacing baseline.
- Compact professional density.
- No decorative marketing art, heavy gradients, oversized illustrations, or inconsistent button treatments.

The output should make Dashboard, Plans, guided setup, Review, Checkout, Provisioning, Subscriptions, and Account visibly belong to the same product.

## Required Code Deliverables

Return implementation-ready code, not only images.

For each screen and reusable component, provide:

- responsive HTML/CSS code or Vue/Tailwind-compatible code;
- component names and suggested file boundaries;
- Frappe UI component mapping where applicable;
- exact token values or CSS variables;
- desktop and mobile layout behavior;
- empty/loading/error/success states;
- keyboard/focus behavior;
- accessible labels and status text;
- copy text for headings, helper text, CTAs, errors, and success messages.

If a visual element cannot be represented by a standard Frappe UI component, mark it as a small custom component and explain why. Prefer Frappe UI primitives for buttons, badges, alerts, inputs, dialogs, and drawers where possible.

## Interaction Requirements

For every primary action, specify:

- label;
- target screen/state;
- loading state;
- success state;
- failure state;
- disabled state;
- mobile behavior;
- focus behavior after action.

Important interactions:

- Dashboard `Choose a Plan` opens Plan browsing.
- Dashboard `View progress` opens the relevant Subscription detail, not a Site page.
- Subscription count/card is interactive and opens Subscriptions.
- Site count/card is informational unless the customer has an obvious ready Site action.
- Plan card click selects the Plan; selected card contains the CTA.
- Entitlement-exhausted Plans remain visible but disabled with helpful copy.
- `Add New Subscription` opens Plan browsing.
- Account avoids duplicating Plan comparison, checkout, provisioning, and runtime details.

## Output Checklist

Return:

- desktop screenshots for all required screens;
- mobile screenshots for all required screens;
- code for all screens and shared components;
- token map;
- component inventory;
- interaction matrix;
- accessibility notes;
- implementation notes for LensCloud/Frappe UI;
- migration notes from the current UI to the redesigned UI;
- a concise design rationale explaining how the new system reduces hesitation and supports revenue conversion.

This is a design handoff track. Canonical implementation scope remains tracked in `docs/platform-workitems.md` under `Customer portal visual coherence redesign`.
