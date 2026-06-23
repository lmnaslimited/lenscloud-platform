import frappe

ENVIRONMENTS = [
    ("Dev", "dev", "development", 10, "Permissive", 0),
    ("QA", "qa", "testing", 20, "Test", 0),
    ("Pre-Prod", "preprod", "staging", 30, "Production-like", 0),
    ("Prod", "prod", "production", 40, "Restricted", 1),
]

CONTROL_PROFILES = {
    "Dev Controls v1": {"protection_level": "Permissive", "enable_developer_mode": 1, "allow_client_scripts": 1, "allow_server_scripts": 1, "enable_bench_test": 1, "require_bench_test": 1, "enable_latp": 1, "require_latp": 1, "latp_mode": "Full"},
    "QA Controls v1": {"protection_level": "Test", "allow_client_scripts": 1, "allow_server_scripts": 1, "enable_bench_test": 1, "require_bench_test": 1, "enable_latp": 1, "require_latp": 1, "latp_mode": "Full"},
    "Pre-Prod Controls v1": {"protection_level": "Production-like", "enable_latp": 1, "require_latp": 1, "latp_mode": "Non-destructive"},
    "Prod Controls v1": {"protection_level": "Restricted", "enable_latp": 1, "require_latp": 1, "latp_mode": "Non-destructive"},
}

LANDSCAPES = {
    "Single Tier": [("Prod", "Prod Controls v1", "prod", "prod")],
    "Two Tier": [("QA", "QA Controls v1", "qa", "qa"), ("Prod", "Prod Controls v1", "prod", "prod")],
    "Three Tier": [("Dev", "Dev Controls v1", "dev", "nonprod"), ("QA", "QA Controls v1", "qa", "nonprod"), ("Prod", "Prod Controls v1", "prod", "prod")],
    "Four Tier": [("Dev", "Dev Controls v1", "dev", "nonprod"), ("QA", "QA Controls v1", "qa", "nonprod"), ("Pre-Prod", "Pre-Prod Controls v1", "preprod", "preprod"), ("Prod", "Prod Controls v1", "prod", "prod")],
}


def upsert(doctype, name, values):
    if frappe.db.exists(doctype, name):
        doc = frappe.get_doc(doctype, name)
        doc.update(values)
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({"doctype": doctype, "name": name, **values})
        doc.insert(ignore_permissions=True)
    return doc


def seed_environments():
    for title, code, tier, sequence, protection, production in ENVIRONMENTS:
        upsert("Environment", title, {"title": title, "code": code, "deployment_tier": tier, "sequence": sequence, "protection_level": protection, "is_production": production, "status": "Active"})
    for title, values in CONTROL_PROFILES.items():
        upsert("Site Control Profile", title, {"title": title, "version": 1, "status": "Active", "cors_policy": "Disabled", **values})
    for title, rows in LANDSCAPES.items():
        values = {"doctype": "Landscape", "title": title, "tier_count": len(rows), "version": 1, "status": "Active", "environments": []}
        for index, (environment, control, bench_group, database_group) in enumerate(rows, 1):
            values["environments"].append({"environment": environment, "site_control_profile": control, "sequence": index * 10, "bench_group": bench_group, "database_group": database_group})
        if frappe.db.exists("Landscape", title):
            doc = frappe.get_doc("Landscape", title); doc.update(values); doc.save(ignore_permissions=True)
        else:
            frappe.get_doc(values).insert(ignore_permissions=True)


def seed_privacy_profiles():
    summaries = {
        "Public": "Cost-efficient shared LensCloud capacity with isolated Site databases.",
        "Private Shared": "Customer-dedicated capacity shared only within your approved environments.",
        "Private": "Dedicated application and database capacity for the strongest isolation.",
    }
    boundaries = {
        "Public": ("Platform", "Platform"),
        "Private Shared": ("Customer", "Customer"),
        "Private": ("Subscription", "Bench"),
    }
    groups = {"Dev": ("dev", "nonprod"), "QA": ("qa", "nonprod"), "Pre-Prod": ("preprod", "preprod"), "Prod": ("prod", "prod")}
    for existing in frappe.get_all("Privacy", pluck="name"):
        if existing not in summaries and not frappe.db.count("Privacy Environment Rule", {"parent": existing}):
            frappe.db.set_value("Privacy", existing, "status", "Draft", update_modified=False)
    for title, summary in summaries.items():
        bench_boundary, database_boundary = boundaries[title]
        doc = upsert("Privacy", title, {"title": title, "version": 1, "status": "Active", "customer_summary": summary})
        doc.set("environment_rules", [])
        for environment, (bench_group, database_group) in groups.items():
            doc.append("environment_rules", {"environment": environment, "bench_boundary": bench_boundary, "bench_group": bench_group, "database_boundary": database_boundary, "database_group": database_group})
        doc.save(ignore_permissions=True)


def seed_free_plan():
    if not frappe.db.exists("Plan", "Free") or not frappe.db.exists("Release Group", "lens-pure"):
        return
    doc = frappe.get_doc("Plan", "Free")
    doc.release_group = "lens-pure"
    doc.landscape = "Single Tier"
    doc.default_privacy_profile = "Public"
    doc.availability = "Public"
    doc.subscription_limit = 1
    doc.site_limit = 1
    doc.status = "Active"
    doc.is_free = 1
    doc.set("allowed_privacy_profiles", [])
    doc.append("allowed_privacy_profiles", {"privacy": "Public"})
    doc.save(ignore_permissions=True)


def seed_sidebar():
    title = "LensCloud Platform"
    doc = frappe.get_doc("Workspace Sidebar", title) if frappe.db.exists("Workspace Sidebar", title) else frappe.new_doc("Workspace Sidebar")
    doc.title = title
    doc.header_icon = "cloud"
    doc.standard = 1
    doc.app = "lenscloud"
    doc.set("items", [])
    groups = [
        ("Home", [("Dashboard", "/lenscloud/platform/dashboard")], False),
        ("Customers and Commerce", [("Customers", "/lenscloud/platform/customers"), ("Plans", "/lenscloud/platform/plans"), ("Subscriptions", "/lenscloud/platform/subscriptions")], False),
        ("Product and Delivery", [("Landscapes", "/lenscloud/platform/landscapes"), ("Environments", "/lenscloud/platform/environments"), ("Site Control Profiles", "/lenscloud/platform/site-control-profiles"), ("Privacy Profiles", "/lenscloud/platform/privacy-profiles"), ("Release Groups", "/lenscloud/platform/release-groups"), ("Releases", "/lenscloud/platform/releases"), ("Apps", "/lenscloud/platform/apps")], True),
        ("Runtime", [("Clusters", "/lenscloud/platform/clusters"), ("Runtime Namespaces", "/lenscloud/platform/runtime-namespaces"), ("Database Servers", "/lenscloud/platform/database-servers"), ("Benches", "/lenscloud/platform/benches"), ("Sites", "/lenscloud/platform/sites")], True),
        ("Operations", [("Test Runs", "/lenscloud/platform/environment-test-runs"), ("Orchestration Logs", "/lenscloud/platform/orchestration-logs")], True),
        ("Configuration", [("Regions", "/lenscloud/platform/regions"), ("Platform Settings", "/lenscloud/platform/settings")], True),
    ]
    for heading, links, closed in groups:
        doc.append("items", {"type": "Section Break", "label": heading, "collapsible": 1, "keep_closed": int(closed)})
        for label, url in links:
            doc.append("items", {"type": "Link", "label": label, "link_type": "URL", "url": url, "child": 1})
    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)


def after_migrate():
    seed_environments()
    seed_privacy_profiles()
    seed_free_plan()
    seed_sidebar()
