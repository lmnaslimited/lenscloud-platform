from __future__ import annotations

import hashlib
import hmac
import time

import frappe
from frappe import _

from lenscloud.api.customer_identity import get_lenscloud_home_page


LOGIN_CODE_PREFIX = "lenscloud:trusted-login:"
REQUEST_NONCE_PREFIX = "lenscloud:trusted-login-nonce:"
LOGIN_CODE_TTL_SECONDS = 60
REQUEST_CLOCK_SKEW_SECONDS = 60


@frappe.whitelist(allow_guest=True, methods=["POST"])
def issue_login_code(user: str):
	"""Issue a single-use login code after verifying the LMNAS server signature."""
	user = str(user or "").strip().lower()

	if not user:
		frappe.throw(_("User is required."), frappe.AuthenticationError)

	_verify_lmnas_request(user)

	user_record = frappe.db.get_value(
		"User",
		user,
		["name", "enabled"],
		as_dict=True,
	)

	if not user_record or not user_record.enabled:
		frappe.throw(
			_("User is disabled or does not exist."),
			frappe.AuthenticationError,
		)

	code = frappe.generate_hash(length=32)

	frappe.cache.set_value(
		f"{LOGIN_CODE_PREFIX}{code}",
		{"user": user_record.name},
		expires_in_sec=LOGIN_CODE_TTL_SECONDS,
	)

	return {
		"code": code,
		"expires_in": LOGIN_CODE_TTL_SECONDS,
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def consume_login_code(code: str):
	"""Consume the one-time code and create a normal LensCloud Frappe session."""
	if not code or len(code) > 128:
		_reject_code()

	login_data = frappe.cache.get_value(
		f"{LOGIN_CODE_PREFIX}{code}",
		expires=True,
	)

	if not login_data:
		_reject_code()

	if isinstance(login_data, str):
		login_data = frappe.parse_json(login_data)

	user = login_data.get("user")

	user_record = frappe.db.get_value(
		"User",
		user,
		["name", "enabled"],
		as_dict=True,
	)

	if not user_record or not user_record.enabled:
		frappe.throw(
			_("User is disabled or does not exist."),
			frappe.AuthenticationError,
		)

	# This is the standard Frappe trusted-login extension point.
	frappe.local.login_manager.login_as(user_record.name)
	frappe.db.commit()

	home_page = get_lenscloud_home_page(user_record.name)

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = f"/{str(home_page).strip().lstrip('/')}"


def _verify_lmnas_request(user: str):
	secret = frappe.conf.get("lmnas_trusted_login_secret")

	if not secret:
		frappe.throw(
			_("Trusted login is not configured."),
			frappe.AuthenticationError,
		)

	timestamp = frappe.get_request_header("X-LMNAS-Timestamp")
	nonce = frappe.get_request_header("X-LMNAS-Nonce")
	signature = frappe.get_request_header("X-LMNAS-Signature")

	if not timestamp or not nonce or not signature:
		frappe.throw(
			_("Missing trusted-login signature."),
			frappe.AuthenticationError,
		)

	try:
		timestamp_number = int(timestamp)
	except (TypeError, ValueError):
		frappe.throw(_("Invalid timestamp."), frappe.AuthenticationError)

	if abs(int(time.time()) - timestamp_number) > REQUEST_CLOCK_SKEW_SECONDS:
		frappe.throw(_("Trusted-login request expired."), frappe.AuthenticationError)

	if len(nonce) > 128:
		frappe.throw(_("Invalid request nonce."), frappe.AuthenticationError)

	nonce_key = f"{REQUEST_NONCE_PREFIX}{nonce}"

	if frappe.cache.get_value(nonce_key):
		frappe.throw(_("Trusted-login request was already used."), frappe.AuthenticationError)

	message = f"{timestamp}\n{nonce}\n{user}"
	expected_signature = hmac.new(
		secret.encode("utf-8"),
		message.encode("utf-8"),
		hashlib.sha256,
	).hexdigest()

	if not hmac.compare_digest(expected_signature, signature):
		frappe.throw(_("Invalid trusted-login signature."), frappe.AuthenticationError)

	frappe.cache.set_value(
		nonce_key,
		1,
		expires_in_sec=REQUEST_CLOCK_SKEW_SECONDS * 2,
	)


def _reject_code():
	frappe.throw(
		_("Invalid or expired login code."),
		frappe.AuthenticationError,
	)