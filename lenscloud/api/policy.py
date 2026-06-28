import hashlib
import json

import frappe
from frappe import _
from frappe.utils import now_datetime


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def policy_hash(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def allowed_privacy_names(plan):
    return {row.privacy for row in plan.get("allowed_privacy_profiles") or [] if row.privacy}


def is_active_submitted_policy(doc):
    return int(doc.docstatus or 0) == 1


def require_active_submitted_policy(doc, label):
    if not is_active_submitted_policy(doc):
        frappe.throw(_("{0} {1} must be a submitted policy document.").format(label, doc.name))


def environment_map(landscape):
    return {row.environment: row for row in landscape.get("environments") or []}


def privacy_rule_map(privacy):
    return {row.environment: row for row in privacy.get("environment_rules") or []}


def resolve_subscription_policy_doc(subscription):
    plan = frappe.get_doc("Plan", subscription.plan)
    landscape = frappe.get_doc("Landscape", plan.landscape)
    privacy = frappe.get_doc("Privacy Profile", plan.default_privacy_profile)
    allowed = allowed_privacy_names(plan)
    if privacy.name not in allowed:
        frappe.throw(_("Default Privacy Profile must be allowed by the Plan."))
    if landscape.status != "Active":
        frappe.throw(_("Plan Landscape must be Active."))
    require_active_submitted_policy(privacy, "Privacy Profile")

    privacy_rules = privacy_rule_map(privacy)
    environments = []
    for row in sorted(landscape.get("environments") or [], key=lambda item: item.sequence or 0):
        environment = frappe.get_doc("Environment", row.environment)
        control = frappe.get_doc("Site Control Profile", row.site_control_profile)
        rule = privacy_rules.get(row.environment)
        if not rule:
            frappe.throw(_("Privacy Profile {0} has no rule for Environment {1}.").format(privacy.name, row.environment))
        if environment.status != "Active":
            frappe.throw(_("Environment {0} must be Active.").format(row.environment))
        require_active_submitted_policy(control, "Site Control Profile")
        environments.append({
            "environment": environment.name,
            "environment_code": environment.code,
            "sequence": row.sequence,
            "deployment_tier": environment.deployment_tier,
            "is_production": bool(environment.is_production),
            "site_control_profile": control.name,
            "site_control_version": control.version,
            "bench_boundary": rule.bench_boundary,
            "bench_group": rule.bench_group or row.bench_group,
            "database_boundary": rule.database_boundary,
            "database_group": rule.database_group or row.database_group,
            "gates": {
                "bench_test": bool(control.enable_bench_test and control.require_bench_test),
                "latp": bool(control.enable_latp and control.require_latp),
                "latp_mode": control.latp_mode,
            },
            "site_controls": {
                "enable_developer_mode": bool(control.enable_developer_mode),
                "allow_client_scripts": bool(control.allow_client_scripts),
                "allow_server_scripts": bool(control.allow_server_scripts),
                "cors_policy": control.cors_policy,
                "cors_origins": [item.strip() for item in (control.cors_origins or "").splitlines() if item.strip()],
            },
        })

    snapshot = {
        "plan": plan.name,
        "release_group": plan.release_group,
        "landscape": landscape.name,
        "landscape_version": landscape.version,
        "privacy_profile": privacy.name,
        "privacy": privacy.privacy,
        "region": subscription.region,
        "environments": environments,
    }
    return snapshot


def apply_subscription_policy(subscription):
    snapshot = resolve_subscription_policy_doc(subscription)
    subscription.release_group = snapshot["release_group"]
    subscription.landscape = snapshot["landscape"]
    subscription.privacy_profile = snapshot["privacy_profile"]
    subscription.effective_policy_snapshot = canonical_json(snapshot)
    subscription.policy_hash = policy_hash(snapshot)
    return snapshot


def snapshot_for(subscription):
    raw = subscription.effective_policy_snapshot or "{}"
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        frappe.throw(_("Subscription Effective Policy Snapshot is invalid JSON."))


def environment_policy(subscription, environment):
    for item in snapshot_for(subscription).get("environments", []):
        if item.get("environment") == environment:
            return item
    frappe.throw(_("Environment {0} is not enabled by Subscription {1}.").format(environment, subscription.name))


def boundary_identity(boundary, subscription, environment=None, site=None, bench=None):
    return {
        "Platform": "platform",
        "Customer": subscription.customer,
        "Subscription": subscription.name,
        "Environment": f"{subscription.name}:{environment}",
        "Site": getattr(site, "name", None),
        "Bench": getattr(bench, "name", None),
    }.get(boundary)


def placement_keys(subscription, environment, site=None, bench=None):
    policy = environment_policy(subscription, environment)
    bench_identity = boundary_identity(policy["bench_boundary"], subscription, environment, site, bench)
    database_identity = boundary_identity(policy["database_boundary"], subscription, environment, site, bench)
    if not bench_identity or not database_identity:
        frappe.throw(_("Unable to resolve Bench or Database isolation boundary."))
    return {
        "bench": f"{policy['bench_boundary']}:{bench_identity}:{policy['bench_group']}",
        "database": f"{policy['database_boundary']}:{database_identity}:{policy['database_group']}",
    }


def get_free_bench(plan, region):
    rows = frappe.get_all("Bench", filters={
        "plan": plan,
        "region": region,
        "environment": "Prod",
        "bench_status": "Ready",
    }, pluck="name", limit=2)
    if not rows:
        frappe.throw(_("No ready Free Plan Bench is available in Region {0}. Contact LensCloud support or choose another Region.").format(region))
    if len(rows) > 1:
        frappe.throw(_("Free Plan capacity is inconsistent: more than one ready Free Bench exists in Region {0}.").format(region))
    return frappe.get_doc("Bench", rows[0])


def latest_passed_test(subscription, environment, release, test_type):
    return frappe.db.exists("Environment Test Run", {
        "subscription": subscription.name,
        "environment": environment,
        "release": release,
        "test_type": test_type,
        "status": "Passed",
        "policy_hash": subscription.policy_hash,
    })


def validate_promotion_gates(subscription, environment, release):
    policy = environment_policy(subscription, environment)
    required = []
    if policy["gates"]["bench_test"]:
        required.append("Bench Test")
    if policy["gates"]["latp"]:
        required.append("LATP")
    missing = [test_type for test_type in required if not latest_passed_test(subscription, environment, release, test_type)]
    if missing:
        frappe.throw(_("Promotion requires current successful tests: {0}.").format(", ".join(missing)))
    return True


@frappe.whitelist()
def preview_subscription_topology(plan, region):
    doc = frappe.new_doc("Subscription")
    doc.plan = plan
    doc.region = region
    doc.customer = frappe.session.user
    snapshot = resolve_subscription_policy_doc(doc)
    return {"policy_hash": policy_hash(snapshot), "topology": snapshot}


@frappe.whitelist()
def approve_subscription(subscription):
    if "System Manager" not in frappe.get_roles():
        frappe.throw(_("Only Platform operators can approve beta subscriptions."), frappe.PermissionError)
    doc = frappe.get_doc("Subscription", subscription)
    if doc.status not in {"Requested", "Pending Approval"}:
        frappe.throw(_("Only requested subscriptions can be approved."))
    doc.status = "Approved"
    doc.approved_by = frappe.session.user
    doc.approved_on = now_datetime()
    doc.save()
    return {"subscription": doc.name, "status": doc.status, "policy_hash": doc.policy_hash}
