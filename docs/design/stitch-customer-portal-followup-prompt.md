# Stitch Follow-Up Prompt: Missing Customer Launch Artifacts

Use this follow-up prompt with Stitch after the first LensCloud customer portal design batch. Do not redesign from legacy screenshots. Use the existing new Stitch screens as continuity references, especially:

- `welcome_to_lenscloud`
- `choose_your_plan`
- `choose_plan_mobile`
- `review_subscription`
- `setup_your_site`
- `launching_your_site`
- `customer_dashboard`
- `my_sites`
- `account_settings`
- `operator_dashboard`

Ignore folders whose names start with `legacy_`; those are only old-product screenshots and must not drive the redesign.

## Objective

Complete the missing design artifacts for the guided Free-first customer launch flow:

1. signup complete / account ready;
2. choose Plan;
3. review Subscription;
4. confirm Free payment;
5. provision Site;
6. open/access Site;
7. land on useful dashboard.

The current design batch covers much of the structure, but implementation needs the missing states, mobile screens, and component-level details below.

## Required New Screens

### 1. Free Checkout Confirmation

Design a checkout-style confirmation screen for the Free Plan.

Must show:

- selected Plan: Free Plan;
- Region;
- Site/subdomain preview;
- line items;
- Plan price: `$0`;
- taxes/fees: `$0` or `Included`;
- total due today: `$0`;
- clear note: `No payment method required for the Free Plan`;
- primary action: `Start Free Subscription`;
- secondary action: `Change Plan`;
- trust/help text explaining the customer can upgrade later.

Do not show a fake credit card form for Free Plan.

### 2. Provisioning State Variants

Design all provisioning variants using the same layout and stepper/progress component:

- loading: request just submitted;
- in progress: normal provisioning;
- delayed: taking longer than expected;
- failed: safe customer-facing failure;
- retry available;
- support needed;
- ready.

Suggested friendly steps:

- `Subscription approved`;
- `Site reserved`;
- `Preparing workspace`;
- `Connecting HTTPS`;
- `Ready to open`.

Do not mention Kubernetes, operator reconcile, Bench, Database Server, namespace, CR, Secret, TLS implementation, pod logs, or action logs.

### 3. Ready / Open Site State

Design the final ready screen after provisioning completes.

Must include:

- Site name;
- Site URL;
- Region;
- current Plan;
- ready status;
- primary action: `Open Site`;
- secondary actions: `View Sites`, `Invite users` coming soon, `Contact support`;
- concise success message that confirms the workspace is ready.

### 4. Mobile Completion Flow

Create mobile versions for these screens:

- Free checkout confirmation;
- provisioning in progress;
- delayed provisioning;
- failed/retry;
- ready/open Site;
- post-launch dashboard.

Mobile must be intentionally designed, not a compressed desktop screenshot. The primary action should stay obvious without hiding important progress.

### 5. Customer Dashboard States

Design dashboard variants for:

- no subscription: primary CTA `Choose a Plan`;
- subscription started but Site not submitted: primary CTA `Continue setup`;
- provisioning: primary CTA `View progress`;
- failed provisioning: primary CTA `Retry` or `Contact support`;
- ready: primary CTA `Open Site`;
- approval pending for paid/beta Plan: primary CTA `View request`.

Use pleasant but restrained cards/infographics for:

- current Plan;
- Subscription status;
- Site status;
- Region;
- Sites count;
- support status;
- next recommended action.

## Required Component Handoff

Provide implementation-ready component guidance for Frappe UI:

- stepper/progress rail component;
- Plan card component;
- checkout summary card;
- status badge variants;
- usage/infographic cards;
- empty state;
- loading state;
- validation error state;
- delayed/progress warning state;
- failed/retry state;
- ready/success state;
- mobile bottom action bar if used.

For each component, specify:

- spacing;
- border radius;
- color token or approximate color;
- typography scale;
- icon usage;
- disabled/loading behavior;
- responsive behavior.

## Required Interaction Notes

For each primary action, provide:

- button label;
- source screen;
- target screen/state;
- loading label;
- success behavior;
- failure behavior;
- validation rules;
- focus behavior after success/failure;
- mobile behavior.

Cover at least:

- `Choose a Plan`;
- `Select Free Plan`;
- `Continue`;
- `Start Free Subscription`;
- `View progress`;
- `Retry`;
- `Contact support`;
- `Open Site`;
- `Change Plan`;
- `Request access` for beta/paid Plans.

## Required Copy Deck

Provide exact copy for:

- screen titles;
- subtitles;
- helper text;
- checkout/free payment explanation;
- provisioning progress labels;
- delayed provisioning message;
- failed provisioning message;
- retry text;
- support text;
- ready/success message;
- access management coming-soon message.

Tone: calm, premium, concise, and confidence-building. Avoid technical implementation language.

## Hard Boundaries

Customers must never see or choose:

- Kubernetes;
- namespaces;
- Benches;
- MariaDB;
- Database Servers;
- Secrets;
- CR names;
- kubeconfig;
- operator terms;
- infrastructure sharing details;
- pod logs;
- action logs;
- TLS/certificate implementation details.

Use customer-safe language:

- Plan;
- Subscription;
- Region;
- Site;
- workspace;
- setup;
- access;
- support;
- progress;
- ready.

## Deliverables

Return:

- desktop screens for all missing states;
- mobile screens for all completion/provisioning states;
- component handoff notes;
- interaction notes;
- copy deck;
- accessibility notes;
- any assumptions or open product questions.
