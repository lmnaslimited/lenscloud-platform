from unittest.mock import patch

import frappe
from frappe.core.doctype.user.user import sign_up
from frappe.tests.utils import FrappeTestCase
from frappe.website.utils import clear_website_cache, get_home_page

from lenscloud.api.customer_identity import (
    customer_doctype_permissions,
    customer_membership_for_user,
    get_lenscloud_home_page,
    provision_customer_for_user,
    require_active_customer_membership,
)
from lenscloud.api.orchestration import ensure_customer_for_user
from lenscloud.setup import (
    DEFAULT_CUSTOMER_ADMIN_ROLE_PROFILE,
    DEFAULT_CUSTOMER_MEMBER_ROLE_PROFILE,
    seed_customer_role_profiles,
)


def unique_email(prefix, domain=None):
    token = frappe.generate_hash(length=8).lower()
    domain = domain or f"{prefix}-{token}.example.com"
    return f"{prefix}-{token}@{domain}", domain


def ensure_region():
    if frappe.db.exists("Region", "EU"):
        return "EU"
    existing = frappe.get_all("Region", filters={"deployment_status": "Active"}, pluck="name", limit=1)
    if existing:
        return existing[0]
    region = frappe.get_doc({
        "doctype": "Region",
        "title": f"Signup Test {frappe.generate_hash(length=5)}",
        "deployment_status": "Active",
        "is_group": 0,
    })
    region.insert(ignore_permissions=True)
    return region.name



def ensure_role_profile(name, role):
    if not frappe.db.exists("Role", role):
        frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)
    if frappe.db.exists("Role Profile", name):
        doc = frappe.get_doc("Role Profile", name)
    else:
        doc = frappe.get_doc({"doctype": "Role Profile", "role_profile": name})
        doc.insert(ignore_permissions=True)
    if role not in [row.role for row in doc.get("roles")]:
        doc.append("roles", {"role": role})
        doc.save(ignore_permissions=True)
    return doc.name

def make_user(email, user_type="Website User", first_name="Launch", last_name="User", signup=True):
    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "enabled": 1,
        "user_type": user_type,
        "send_welcome_email": 0,
        "new_password": frappe.generate_hash(length=12),
    })
    user.flags.ignore_password_policy = True
    if signup:
        user.flags.lenscloud_signup_provision_customer = True
    user.insert(ignore_permissions=True)
    return user


class TestCustomerIdentity(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.region = ensure_region()
        token = frappe.generate_hash(length=6)
        cls.admin_role = f"LC Test Customer Admin {token}"
        cls.member_role = f"LC Test Customer Member {token}"
        cls.admin_profile = ensure_role_profile(f"LC Test Customer Admin Profile {token}", cls.admin_role)
        cls.member_profile = ensure_role_profile(f"LC Test Customer Member Profile {token}", cls.member_role)
        if frappe.db.exists("DocType", "Platform Settings"):
            frappe.db.set_single_value("Platform Settings", "default_signup_region", cls.region)
            frappe.db.set_single_value("Platform Settings", "default_customer_admin_role_profile", cls.admin_profile)
            frappe.db.set_single_value("Platform Settings", "default_customer_member_role_profile", cls.member_profile)

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def test_standard_customer_role_profiles_are_seeded(self):
        seed_customer_role_profiles()
        for profile_name in (DEFAULT_CUSTOMER_ADMIN_ROLE_PROFILE, DEFAULT_CUSTOMER_MEMBER_ROLE_PROFILE):
            self.assertTrue(frappe.db.exists("Role", profile_name))
            self.assertTrue(frappe.db.exists("Role Profile", profile_name))
            profile = frappe.get_doc("Role Profile", profile_name)
            self.assertIn(profile_name, [row.role for row in profile.get("roles")])

    def test_native_frappe_signup_creates_customer_owner(self):
        email, domain = unique_email("native-signup")
        frappe.set_user("Guest")
        with patch("frappe.core.doctype.user.user.is_signup_disabled", return_value=False):
            sign_up(email, "Native Signup", "")
        frappe.set_user("Administrator")

        membership = customer_membership_for_user(email)
        self.assertIsNotNone(membership)
        self.assertEqual(membership.status, "Active")
        self.assertEqual(membership.member_role, "Owner")
        customer = frappe.get_doc("Customer", membership.customer)
        self.assertEqual(customer.user, email)
        self.assertEqual(customer.primary_domain, domain)

    def test_first_company_domain_signup_creates_customer_owner(self):
        email, domain = unique_email("owner")
        user = make_user(email, first_name="First", last_name="Owner")

        membership = customer_membership_for_user(user.name)
        self.assertIsNotNone(membership)
        self.assertEqual(membership.status, "Active")
        self.assertEqual(membership.member_role, "Owner")
        self.assertEqual(membership.is_primary_owner, 1)

        customer = frappe.get_doc("Customer", membership.customer)
        self.assertEqual(customer.user, user.name)
        self.assertEqual(customer.primary_domain, domain)
        self.assertEqual(customer.signup_source, "Signup")

    def test_signup_assigns_role_profile_and_customer_user_permission(self):
        email, _domain = unique_email("rbac-owner")
        user = make_user(email, first_name="RBAC", last_name="Owner")
        membership = customer_membership_for_user(user.name)

        user_doc = frappe.get_doc("User", user.name)
        self.assertIn(self.admin_profile, [row.role_profile for row in user_doc.get("role_profiles")])
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": user.name,
            "allow": "Customer",
            "for_value": membership.customer,
            "apply_to_all_doctypes": 1,
        }))

        second_email = f"rbac-member-{frappe.generate_hash(length=8).lower()}@{email.rsplit('@', 1)[1]}"
        member = make_user(second_email, first_name="RBAC", last_name="Member")
        member_doc = frappe.get_doc("User", member.name)
        member_membership = customer_membership_for_user(member.name)

        self.assertEqual(member_membership.customer, membership.customer)
        self.assertEqual(member_membership.status, "Pending")
        self.assertIn(self.member_profile, [row.role_profile for row in member_doc.get("role_profiles")])
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": member.name,
            "allow": "Customer",
            "for_value": membership.customer,
            "apply_to_all_doctypes": 1,
        }))

    def test_signup_uses_conventional_role_profiles_when_settings_are_blank(self):
        frappe.db.set_single_value("Platform Settings", "default_customer_admin_role_profile", "")
        frappe.db.set_single_value("Platform Settings", "default_customer_member_role_profile", "")
        seed_customer_role_profiles()

        email, _domain = unique_email("fallback-owner")
        user = make_user(email, first_name="Fallback", last_name="Owner")
        membership = customer_membership_for_user(user.name)

        user_doc = frappe.get_doc("User", user.name)
        self.assertIn("LensCloud Customer Admin", [row.role_profile for row in user_doc.get("role_profiles")])
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": user.name,
            "allow": "Customer",
            "for_value": membership.customer,
            "apply_to_all_doctypes": 1,
        }))
        self.assertTrue(customer_doctype_permissions(user.name).get("Capability", {}).get("read"))

        second_email = f"fallback-member-{frappe.generate_hash(length=8).lower()}@{email.rsplit('@', 1)[1]}"
        member = make_user(second_email, first_name="Fallback", last_name="Member")
        member_doc = frappe.get_doc("User", member.name)
        member_membership = customer_membership_for_user(member.name)

        self.assertEqual(member_membership.customer, membership.customer)
        self.assertEqual(member_membership.status, "Pending")
        self.assertIn("LensCloud Customer Member", [row.role_profile for row in member_doc.get("role_profiles")])
        self.assertTrue(frappe.db.exists("User Permission", {
            "user": member.name,
            "allow": "Customer",
            "for_value": membership.customer,
            "apply_to_all_doctypes": 1,
        }))

    def test_second_same_domain_signup_is_pending_member(self):
        first_email, domain = unique_email("domain-owner")
        first = make_user(first_email, first_name="Domain", last_name="Owner")
        first_membership = customer_membership_for_user(first.name)

        second_email = f"colleague-{frappe.generate_hash(length=8).lower()}@{domain}"
        second = make_user(second_email, first_name="Domain", last_name="Member")
        second_membership = customer_membership_for_user(second.name)

        self.assertEqual(second_membership.customer, first_membership.customer)
        self.assertEqual(second_membership.status, "Pending")
        self.assertEqual(second_membership.member_role, "Member")
        self.assertEqual(second_membership.is_primary_owner, 0)
        self.assertEqual(
            frappe.db.count("Customer", {"primary_domain": domain}),
            1,
        )

    def test_public_email_signup_creates_individual_customer(self):
        email = f"free-{frappe.generate_hash(length=8).lower()}@gmail.com"
        user = make_user(email, first_name="Public", last_name="Email")

        membership = customer_membership_for_user(user.name)
        customer = frappe.get_doc("Customer", membership.customer)
        self.assertEqual(membership.status, "Active")
        self.assertEqual(membership.member_role, "Owner")
        self.assertFalse(customer.primary_domain)
        self.assertEqual(customer.user, user.name)


    def test_legacy_customer_without_domain_does_not_capture_new_signup(self):
        legacy_email, domain = unique_email("legacy-owner")
        legacy_user = make_user(legacy_email, first_name="Legacy", last_name="Owner", signup=False)
        legacy_customer = frappe.get_doc({
            "doctype": "Customer",
            "first_name": "Legacy",
            "last_name": "Customer",
            "user": legacy_user.name,
            "region": self.region,
            "signup_source": "Signup",
        }).insert(ignore_permissions=True)

        new_email = f"new-{frappe.generate_hash(length=8).lower()}@{domain}"
        new_user = make_user(new_email, first_name="New", last_name="Owner")
        membership = customer_membership_for_user(new_user.name)

        self.assertNotEqual(membership.customer, legacy_customer.name)
        self.assertEqual(membership.status, "Active")
        self.assertEqual(membership.member_role, "Owner")
        self.assertEqual(membership.is_primary_owner, 1)

    def test_lenscloud_home_page_keeps_customer_users_out_of_me(self):
        email, _domain = unique_email("home")
        user = make_user(email, first_name="Home", last_name="Customer")
        clear_website_cache()
        frappe.cache.hdel("home_page", user.name)
        frappe.set_user(user.name)

        self.assertEqual(get_lenscloud_home_page(user.name), "lenscloud/customer/dashboard")
        self.assertEqual(get_home_page(), "lenscloud/customer/dashboard")

    def test_lenscloud_home_page_routes_platform_users_to_platform(self):
        email, _domain = unique_email("home-platform")
        user = make_user(email, user_type="System User", first_name="Home", last_name="Platform", signup=False)
        user.add_roles("System Manager")
        clear_website_cache()
        frappe.cache.hdel("home_page", user.name)
        frappe.set_user(user.name)

        self.assertEqual(get_lenscloud_home_page(user.name), "lenscloud/platform/dashboard")
        self.assertEqual(get_home_page(), "lenscloud/platform/dashboard")

    def test_system_user_does_not_create_customer_membership(self):
        email, _domain = unique_email("system")
        user = make_user(email, user_type="System User", first_name="Platform", last_name="Operator", signup=False)

        self.assertIsNone(customer_membership_for_user(user.name))
        self.assertFalse(frappe.db.exists("Customer", {"user": user.name}))
        user.add_roles("System Manager")
        self.assertIsNone(provision_customer_for_user(user.name))

    def test_pending_same_domain_member_cannot_provision(self):
        owner_email, domain = unique_email("pending-owner")
        owner = make_user(owner_email, first_name="Pending", last_name="Owner")
        owner_membership = customer_membership_for_user(owner.name)
        self.assertEqual(require_active_customer_membership(owner.name).customer, owner_membership.customer)

        pending_email = f"pending-{frappe.generate_hash(length=8).lower()}@{domain}"
        pending = make_user(pending_email, first_name="Pending", last_name="Member")
        pending_membership = customer_membership_for_user(pending.name)
        self.assertEqual(pending_membership.status, "Pending")

        frappe.set_user(pending.name)
        with self.assertRaises(frappe.PermissionError):
            ensure_customer_for_user(self.region)
