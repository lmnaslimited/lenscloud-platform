import hashlib
import hmac
import time
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from lenscloud.api.trusted_login import (
	LOGIN_CODE_PREFIX,
	consume_login_code,
	issue_login_code,
)


class TestTrustedLogin(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_invalid_login_code_is_rejected(self):
		frappe.set_user("Guest")

		with self.assertRaises(frappe.AuthenticationError):
			consume_login_code("invalid")

	def test_login_code_is_single_use(self):
		email = self._make_user()
		code = frappe.generate_hash(length=32)
		key = f"{LOGIN_CODE_PREFIX}{code}"

		frappe.cache.set_value(
			key,
			{"user": email},
			expires_in_sec=60,
		)

		frappe.set_user("Guest")
		consume_login_code(code)

		self.assertFalse(frappe.cache.get_value(key))

	def test_signed_server_request_issues_code(self):
		email = self._make_user()
		secret = "test-trusted-login-secret"
		timestamp = str(int(time.time()))
		nonce = frappe.generate_hash(length=20)
		message = f"{timestamp}\n{nonce}\n{email}"
		signature = hmac.new(
			secret.encode(),
			message.encode(),
			hashlib.sha256,
		).hexdigest()

		headers = {
			"X-LMNAS-Timestamp": timestamp,
			"X-LMNAS-Nonce": nonce,
			"X-LMNAS-Signature": signature,
		}

		with (
			patch.dict(frappe.conf, {"lmnas_trusted_login_secret": secret}),
			patch("frappe.get_request_header", side_effect=headers.get),
		):
			result = issue_login_code(email)

		self.assertTrue(result["code"])

	def _make_user(self):
		email = f"trusted-{frappe.generate_hash(length=8).lower()}@example.com"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Trusted",
				"last_name": "Login",
				"enabled": 1,
				"user_type": "Website User",
				"send_welcome_email": 0,
				"new_password": frappe.generate_hash(length=16),
			}
		)
		user.flags.ignore_password_policy = True
		user.insert(ignore_permissions=True)
		return user.name