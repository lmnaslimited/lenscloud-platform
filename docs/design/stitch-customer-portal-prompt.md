# Stitch Customer Portal Design Prompt

Use this prompt with Stitch and attach current LensCloud customer and Platform screenshots as structural references. The goal is not to decorate the current screens; the goal is to redesign the customer onboarding journey so a first-time customer always knows the next action.

## Stitch Prompt

Redesign LensCloud as a responsive SaaS customer portal using Frappe UI and Frappe CRM visual conventions. Use the supplied current screens only as structural references, but simplify and modernize the experience substantially.

The primary flow starts after a customer signs up from `lmnas.com` and lands inside LensCloud Platform. Design this as a guided activity, not as disconnected pages. The customer should move through clear steps:

1. **Welcome / Account Ready**
   - Confirm the customer is signed in.
   - Show the customer or company name if available.
   - Explain that LensCloud Platform is where they choose a Plan, launch their Site, invite users later, and access their Sites.
   - Primary action: `Choose a Plan`.

2. **Choose Plan**
   - Show Plan cards that are easy to compare.
   - Free Plan must be visually obvious and recommended for launch.
   - Paid/beta Plans may be shown as `Request access` or `Coming soon`; do not fake paid checkout.
   - Cards should show customer-facing outcomes only: price, included Site count, environments, support level, approval requirement, and a friendly isolation summary.
   - Customers must not see Kubernetes, namespaces, Benches, MariaDB, CR names, Secrets, or infrastructure sharing details.

3. **Subscription Review**
   - Summarize selected Plan, Region, Site/subdomain, and included features.
   - Make the Subscription concept friendly: `Your LensCloud service subscription`.
   - For the Free Plan, show payment as a real step but clearly state `$0 due today`, `No payment method required`, and `Free Plan`.
   - For paid/beta Plans, show `Approval required` or `Payment coming later`; do not design a fake card-payment form for this pass.

4. **Confirm Free Payment**
   - Include a clean checkout-style confirmation screen for Free Plan.
   - Show line items: Plan price, taxes/fees if any as zero, total due today as zero.
   - Primary action: `Start Free Subscription`.
   - Secondary action: `Change Plan`.

5. **Provision Site**
   - After subscription confirmation, show an automatic provisioning timeline.
   - Steps should include friendly labels such as `Subscription approved`, `Site reserved`, `Preparing workspace`, `Connecting HTTPS`, and `Ready to open`.
   - Do not mention Kubernetes apply, operator reconcile, Bench, Database Server, namespace, CR, Secret, or wildcard TLS internals.
   - Include retry/recovery states that tell the customer what to do next without exposing infrastructure logs.

6. **Access Site**
   - Ready state should have one obvious primary action: `Open Site`.
   - Show Site URL, status, Region, Plan, and next helpful actions.
   - Include future placeholders for `Invite users`, `Manage access`, and `Contact support`, but label them as coming soon or Platform-managed if not implemented.

7. **Customer Dashboard After Launch**
   - Dashboard should be visually pleasant and confidence-building.
   - Use restrained colors, Frappe tokens, compact cards, small infographics, and clear progress/status summaries.
   - Show usage-style cards such as Sites, ready Sites, current Plan, Region, subscription state, and support status.
   - Use one primary action depending on state:
     - no subscription: `Choose a Plan`;
     - provisioning: `View progress`;
     - ready: `Open Site`.

Design desktop and mobile screens for the complete flow. The mobile flow should feel intentionally designed, not just compressed desktop.

## Visual Direction

- Keep it recognizably Frappe-native: clean surfaces, compact typography, restrained cards, badges, status strips, tabs, dialogs, and simple form controls.
- Pleasant color is welcome, but avoid gradients, decorative marketing art, oversized empty-state illustrations, and overly playful visuals.
- Use accessible contrast and clear text over decorative flair.
- Prefer one guided flow container with a stepper/progress rail over scattered page sections.
- The customer should always see: where they are, what they selected, what happens next, and how to recover from a problem.

## Required Screens

- Post-signup welcome / account-ready screen.
- Plan selection screen.
- Plan comparison cards.
- Free Plan subscription review.
- Free checkout confirmation showing `$0 due today` and `No payment method required`.
- Region and subdomain setup.
- Provisioning progress: loading, in progress, delayed, failed/retry, and ready.
- Ready dashboard with `Open Site` primary action.
- Sites list/detail for customers.
- Account page with identity/access placeholders.
- Beta or paid Plan request-access state.
- Mobile versions of all critical screens.

## Required Component States

Provide reusable component states for:

- loading;
- empty;
- validation error;
- plan selected;
- subscription pending;
- free checkout confirmed;
- provisioning;
- delayed provisioning;
- ready;
- failed with retry/contact support;
- approval pending;
- payment not required;
- payment future/unavailable;
- access management coming soon.

## Platform Companion Screens

Also propose compact Platform operator screens for:

- launch readiness dashboard;
- Free Plan capacity by Region;
- pending subscription approvals;
- customer subscription detail;
- customer Site provisioning timeline;
- grouped/collapsible sidebar.

## Interaction Notes

For every primary action, specify:

- button label;
- target screen/state;
- loading behavior;
- success behavior;
- failure copy;
- empty-state copy;
- mobile behavior;
- keyboard/focus behavior.

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
- pod logs or action logs.

Use friendly language such as Plan, Subscription, Region, Site, workspace, setup, access, support, and progress.

## Required Deliverables

- Desktop and mobile screens for the guided signup-to-Site journey.
- Frappe UI component inventory and reusable states.
- A concise design rationale explaining how the flow reduces customer confusion.
- Accessibility annotations for focus order, keyboard use, contrast, status text, and error recovery.
- Copy deck for all step titles, helper text, button labels, error messages, and success states.
- A Platform companion dashboard concept for operators.

This is a design track. The canonical implementation backlog remains `docs/platform-workitems.md`.
