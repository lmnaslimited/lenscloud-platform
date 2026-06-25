import frappe
from frappe import _
from frappe.utils import now_datetime

from lenscloud.api.orchestration import get_platform_settings


def require_platform():
    if not ({"System Manager", "LensCloud Platform User"} & set(frappe.get_roles())):
        frappe.throw(_("Platform access is required."), frappe.PermissionError)


@frappe.whitelist()
def get_platform_dashboard():
    require_platform()
    settings = get_platform_settings()
    free_plans = frappe.db.count("Plan", {"status": "Active", "is_free": 1})
    public_benches = frappe.db.count("Bench", {"bench_status": "Ready", "privacy": "Public", "environment": "Prod"})
    active_clusters = frappe.db.count("Cluster", {"status": "Active", "health_status": "Healthy"})
    signup_disabled = frappe.db.get_single_value("Website Settings", "disable_signup") or 0
    metrics = {
        "customers": frappe.db.count("Customer"),
        "subscriptions": frappe.db.count("Subscription", {"status": ["not in", ["Cancelled", "Failed"]]}),
        "provisioning_sites": frappe.db.count("Site", {"site_status": ["in", ["Requested", "Accepted", "Provisioning"]]}),
        "ready_sites": frappe.db.count("Site", {"site_status": ["in", ["Ready", "Active"]]}),
    }
    action_required = {
        "failed_sites": frappe.db.count("Site", {"site_status": ["in", ["Failed", "Deletion Failed"]]}),
        "pending_approvals": frappe.db.count("Subscription", {"status": "Pending Approval"}),
        "failed_tests": frappe.db.count("Environment Test Run", {"status": "Failed"}),
        "failed_actions": frappe.db.count("Orchestration Action Log", {"status": "Failed"}),
    }
    capacity = []
    for region in frappe.get_all("Region", filters={"deployment_status": "Active"}, fields=["name", "title", "cluster"], order_by="lft asc"):
        capacity.append({
            **region,
            "free_benches": frappe.db.count("Bench", {"region": region.name, "bench_status": "Ready", "privacy": "Public", "environment": "Prod"}),
            "ready_benches": frappe.db.count("Bench", {"region": region.name, "bench_status": "Ready"}),
            "ready_databases": frappe.db.count("Database Server", {"region": region.name, "database_status": "Ready"}),
            "ready_sites": frappe.db.count("Site", {"region": region.name, "site_status": ["in", ["Ready", "Active"]]}),
        })
    recent_actions = frappe.get_all("Orchestration Action Log", fields=["name", "title", "status", "resource_kind", "operation", "modified"], order_by="modified desc", limit=8)
    gates = [
        {"key": "signup", "label": "Customer signup", "ready": not bool(signup_disabled), "message": "Enabled" if not signup_disabled else "Disabled in Website Settings"},
        {"key": "free-plan", "label": "Active Free Plan", "ready": free_plans > 0, "message": f"{free_plans} active"},
        {"key": "root-domain", "label": "Wildcard root domain", "ready": bool(settings.root_domain), "message": settings.root_domain or "Not configured"},
        {"key": "public-capacity", "label": "Free public capacity", "ready": public_benches > 0, "message": f"{public_benches} ready Free/Public benches"},
        {"key": "cluster", "label": "Healthy active cluster", "ready": active_clusters > 0, "message": f"{active_clusters} healthy"},
        {"key": "apply", "label": "Kubernetes apply", "ready": bool(settings.kubernetes_apply_enabled), "message": "Enabled" if settings.kubernetes_apply_enabled else "Disabled"},
    ]
    return {"metrics": metrics, "gates": gates, "action_required": action_required, "capacity": capacity, "recent_actions": recent_actions, "launch_ready": all(item["ready"] for item in gates if item["key"] != "apply")}


@frappe.whitelist()
def get_navigation(scope="platform"):
    if scope == "platform":
        require_platform()
    elif frappe.session.user == "Guest":
        frappe.throw(_("Authentication is required."), frappe.PermissionError)
    title = "LensCloud Platform" if scope == "platform" else "LensCloud Customer"
    if not frappe.db.exists("Workspace Sidebar", title):
        return []
    doc = frappe.get_doc("Workspace Sidebar", title)
    groups = []
    current = None
    for row in doc.get("items") or []:
        if row.type in {"Section Break", "Sidebar Item Group"}:
            current = {"heading": row.label, "collapsible": bool(row.collapsible), "keep_closed": bool(row.keep_closed), "items": []}
            groups.append(current)
        elif row.type == "Link" and row.link_type == "URL" and row.url:
            if current is None:
                current = {"heading": "Navigation", "collapsible": False, "keep_closed": False, "items": []}
                groups.append(current)
            current["items"].append({"key": frappe.scrub(row.label), "label": row.label, "route": row.url.removeprefix("/lenscloud"), "icon": row.icon})
    return groups


@frappe.whitelist()
def request_beta_enrollment(plan, region):
    user = frappe.session.user
    if user == "Guest":
        frappe.throw(_("Authentication is required."), frappe.PermissionError)
    plan_doc = frappe.get_doc("Plan", plan)
    if plan_doc.availability != "Beta" or plan_doc.status != "Active":
        frappe.throw(_("This Plan is not accepting beta enrollment."))
    customer = frappe.db.get_value("Customer", {"user": user}, "name")
    if not customer:
        frappe.throw(_("Complete customer onboarding before requesting beta enrollment."))
    existing = frappe.db.exists("Subscription", {"customer": customer, "plan": plan, "status": ["not in", ["Cancelled", "Failed"]]})
    if existing:
        return {"subscription": existing, "status": frappe.db.get_value("Subscription", existing, "status")}
    doc = frappe.get_doc({"doctype": "Subscription", "customer": customer, "plan": plan, "region": region, "status": "Pending Approval", "effective_from": now_datetime()})
    doc.insert(ignore_permissions=True)
    return {"subscription": doc.name, "status": doc.status, "policy_hash": doc.policy_hash}

_LAYOUT_FIELDTYPES = {"Tab Break", "Section Break", "Column Break"}

def _editor_field(df):
    value = {
        "fieldname": df.fieldname,
        "label": df.label or df.fieldname,
        "fieldtype": df.fieldtype,
        "options": df.options,
        "required": bool(df.reqd),
        "read_only": bool(df.read_only),
        "hidden": bool(df.hidden),
        "default": df.default,
        "description": df.description,
        "collapsible": bool(df.collapsible),
    }
    if df.fieldtype in {"Table", "Table MultiSelect"} and df.options:
        child = frappe.get_meta(df.options)
        value["columns"] = [
            _editor_field(child_df)
            for child_df in child.fields
            if child_df.fieldtype not in _LAYOUT_FIELDTYPES and not child_df.hidden
        ]
    elif df.fieldtype == "Link" and df.options:
        value["target_is_submittable"] = bool(frappe.get_meta(df.options).is_submittable)
    return value


@frappe.whitelist()
def get_doctype_editor_schema(doctype):
    require_platform()
    meta = frappe.get_meta(doctype)
    if meta.module != "Lenscloud":
        frappe.throw(_("Only LensCloud document metadata is available."), frappe.PermissionError)
    autoname = meta.autoname or ""
    naming_field = autoname.removeprefix("field:") if autoname.startswith("field:") else None
    return {
        "doctype": meta.name,
        "title_field": meta.title_field,
        "autoname": autoname,
        "naming_field": naming_field,
        "allow_rename": bool(meta.allow_rename),
        "is_submittable": bool(meta.is_submittable),
        "can_read": bool(frappe.has_permission(doctype, "read")),
        "can_create": bool(frappe.has_permission(doctype, "create")),
        "can_write": bool(frappe.has_permission(doctype, "write")),
        "links": [
            {
                "group": link.group or "Related",
                "link_doctype": link.link_doctype,
                "link_fieldname": link.link_fieldname,
                "table_fieldname": link.table_fieldname,
            }
            for link in meta.links or []
            if link.link_doctype and link.link_fieldname
        ],
        "fields": [_editor_field(df) for df in meta.fields if not df.hidden],
    }

def _connection_preview_fields(meta):
    fields = ["name"]
    if meta.title_field and meta.has_field(meta.title_field):
        fields.append(meta.title_field)
    for df in meta.fields:
        if len(fields) >= 4:
            break
        if df.in_list_view and df.fieldtype not in _LAYOUT_FIELDTYPES | {"Table", "Table MultiSelect"}:
            fields.append(df.fieldname)
    return list(dict.fromkeys(fields))


@frappe.whitelist()
def get_document_connections(doctype, name):
    require_platform()
    meta = frappe.get_meta(doctype)
    if meta.module != "Lenscloud":
        frappe.throw(_("Only LensCloud document connections are available."), frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    doc.check_permission("read")
    connections = []
    for link in meta.links or []:
        if not link.link_doctype or not link.link_fieldname or link.table_fieldname:
            continue
        if not frappe.has_permission(link.link_doctype, "read"):
            continue
        linked_meta = frappe.get_meta(link.link_doctype)
        filters = {link.link_fieldname: name}
        count_rows = frappe.get_list(link.link_doctype, filters=filters, fields=[{"COUNT": "*"}], limit=1)
        count = int((next(iter(count_rows[0].values())) if count_rows else 0) or 0)
        items = frappe.get_list(
            link.link_doctype,
            filters=filters,
            fields=_connection_preview_fields(linked_meta),
            order_by="modified desc",
            limit=5,
        )
        connections.append({
            "group": link.group or "Related",
            "label": linked_meta.name,
            "doctype": linked_meta.name,
            "link_field": link.link_fieldname,
            "count": count,
            "items": items,
        })
    return connections
