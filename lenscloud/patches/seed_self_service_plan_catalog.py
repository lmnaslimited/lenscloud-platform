import json

import frappe


def execute():
    release_group = frappe.db.exists("Release Group", "lens-pure")
    landscapes = {
        "single": frappe.db.exists("Landscape", "Single Tier"),
        "two": frappe.db.exists("Landscape", "Two Tier"),
        "three": frappe.db.exists("Landscape", "Three Tier"),
        "four": frappe.db.exists("Landscape", "Four Tier"),
    }
    privacy_profiles = {
        "public": _default_privacy_profile("Public"),
        "private_shared": _default_privacy_profile("Private Shared"),
        "private": _default_privacy_profile("Private"),
    }
    if not release_group or not all(landscapes.values()) or not all(privacy_profiles.values()):
        frappe.log_error(
            title="LensCloud Plan catalog seed skipped",
            message="Missing lens-pure Release Group, active Landscapes, or submitted default Privacy Profiles.",
        )
        return

    specs = [
        {
            "title": "Tier 1 Free",
            "aliases": ["Free"],
            "plan_code": "tier-1-free",
            "status": "Active",
            "is_default": 1,
            "is_free": 1,
            "monthly_price": "0",
            "billing_frequency": "Monthly",
            "site_limit": "1",
            "subscription_limit": 1,
            "bench_policy": "Shared Bench",
            "availability": "Public",
            "release_group": release_group,
            "landscape": landscapes["single"],
            "default_privacy_profile": privacy_profiles["public"],
            "allowed_privacy_profiles": [privacy_profiles["public"]],
            "publish_in_customer_portal": 1,
            "show_draft_in_customer_portal": 0,
            "allow_self_service": 1,
            "request_access_only": 0,
            "experimental": 0,
            "portal_badge": "Recommended",
            "portal_sort_order": 20,
            "description": "Launch one production LensCloud Site with the Free Plan.",
            "portal_feature_json": [
                {"icon": "globe", "feature": "One production Site"},
                {"icon": "credit-card", "feature": "$0 due today"},
                {"icon": "shield", "feature": "Public starter placement"},
                {"icon": "sparkles", "feature": "Guided setup included"},
            ],
        },
        {
            "title": "Tier 2 Growth",
            "aliases": [],
            "plan_code": "tier-2-growth",
            "status": "Active",
            "is_default": 0,
            "is_free": 0,
            "monthly_price": "0",
            "billing_frequency": "Monthly",
            "site_limit": "2",
            "subscription_limit": 1,
            "bench_policy": "Dedicated Bench",
            "availability": "Beta",
            "release_group": release_group,
            "landscape": landscapes["two"],
            "default_privacy_profile": privacy_profiles["private_shared"],
            "allowed_privacy_profiles": [privacy_profiles["private_shared"]],
            "publish_in_customer_portal": 1,
            "show_draft_in_customer_portal": 0,
            "allow_self_service": 0,
            "request_access_only": 1,
            "experimental": 0,
            "portal_badge": "Request access",
            "portal_sort_order": 10,
            "description": "Separate quality and production flow for growing teams.",
            "portal_feature_json": [
                {"icon": "layers", "feature": "QA and Production environments"},
                {"icon": "users", "feature": "Team launch review"},
                {"icon": "shield", "feature": "Customer-scoped placement"},
                {"icon": "life-buoy", "feature": "Approval-assisted onboarding"},
            ],
        },
        {
            "title": "Tier 3 Scale",
            "aliases": [],
            "plan_code": "tier-3-scale",
            "status": "Active",
            "is_default": 0,
            "is_free": 0,
            "monthly_price": "0",
            "billing_frequency": "Monthly",
            "site_limit": "3",
            "subscription_limit": 1,
            "bench_policy": "Dedicated Bench",
            "availability": "Beta",
            "release_group": release_group,
            "landscape": landscapes["three"],
            "default_privacy_profile": privacy_profiles["private"],
            "allowed_privacy_profiles": [privacy_profiles["private"]],
            "publish_in_customer_portal": 1,
            "show_draft_in_customer_portal": 0,
            "allow_self_service": 0,
            "request_access_only": 1,
            "experimental": 1,
            "portal_badge": "Beta",
            "portal_sort_order": 30,
            "description": "Dev, QA, and Production flow for teams planning safer releases.",
            "portal_feature_json": [
                {"icon": "workflow", "feature": "Dev, QA, and Production environments"},
                {"icon": "shield", "feature": "Private customer placement"},
                {"icon": "check-circle", "feature": "Release promotion ready"},
                {"icon": "life-buoy", "feature": "Platform approval required"},
            ],
        },
        {
            "title": "Tier 4 Enterprise",
            "aliases": [],
            "plan_code": "tier-4-enterprise",
            "status": "Active",
            "is_default": 0,
            "is_free": 0,
            "monthly_price": "0",
            "billing_frequency": "Monthly",
            "site_limit": "4",
            "subscription_limit": 1,
            "bench_policy": "Manual Placement",
            "availability": "Invite Only",
            "release_group": release_group,
            "landscape": landscapes["four"],
            "default_privacy_profile": privacy_profiles["private"],
            "allowed_privacy_profiles": [privacy_profiles["private"]],
            "publish_in_customer_portal": 0,
            "show_draft_in_customer_portal": 0,
            "allow_self_service": 0,
            "request_access_only": 1,
            "experimental": 1,
            "portal_badge": "Invite only",
            "portal_sort_order": 40,
            "description": "Four-environment enterprise rollout. Not available for self-service launch yet.",
            "portal_feature_json": [
                {"icon": "building", "feature": "Four environment rollout"},
                {"icon": "shield", "feature": "Enterprise placement policy"},
                {"icon": "users", "feature": "Account-led onboarding"},
                {"icon": "life-buoy", "feature": "Invite-only availability"},
            ],
        },
    ]
    for spec in specs:
        _upsert_plan(spec)


def _default_privacy_profile(privacy):
    return frappe.db.get_value(
        "Privacy Profile",
        {"privacy": privacy, "is_default": 1, "docstatus": 1},
        "name",
    )


def _upsert_plan(spec):
    name = frappe.db.exists("Plan", {"plan_code": spec["plan_code"]})
    if not name:
        for alias in spec.get("aliases", []):
            name = frappe.db.exists("Plan", alias)
            if name:
                break
    if name:
        plan = frappe.get_doc("Plan", name)
        if plan.docstatus == 1:
            if plan.plan_code != spec["plan_code"]:
                frappe.log_error(
                    title="LensCloud Plan catalog seed skipped submitted Plan",
                    message=f"Plan {plan.name} is submitted with plan_code {plan.plan_code}; expected {spec['plan_code']}.",
                )
            return
        if plan.docstatus == 2:
            existing_active = frappe.db.exists("Plan", {"plan_code": spec["plan_code"], "docstatus": 1})
            if existing_active:
                return
            plan = frappe.get_doc({"doctype": "Plan", **_plan_values(spec)})
            plan.insert(ignore_permissions=True)
        else:
            plan.update(_plan_values(spec))
            plan.flags.ignore_mandatory = True
            plan.save(ignore_permissions=True)
    else:
        plan = frappe.get_doc({"doctype": "Plan", **_plan_values(spec)})
        plan.insert(ignore_permissions=True)
    if plan.docstatus == 0 and spec["status"] == "Active":
        plan.submit()


def _plan_values(spec):
    values = {key: value for key, value in spec.items() if key not in {"aliases", "allowed_privacy_profiles", "portal_feature_json"}}
    values["portal_feature_json"] = json.dumps(spec["portal_feature_json"], indent=2)
    values["allowed_privacy_profiles"] = [{"privacy": name} for name in spec["allowed_privacy_profiles"]]
    return values
