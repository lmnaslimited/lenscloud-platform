import frappe
from urllib.parse import urlparse

@frappe.whitelist(allow_guest=True)
def get_google_auth_link(i_redirect_to_nextjs: str = None):
    """
    Exposes Frappe's internal OAuth authorization URL generation for website users.

    Frappe's `get_oauth2_authorize_url` builds the required OAuth `code` and
    `state` flow but is not whitelisted. This endpoint provides guest access to
    that functionality while validating the requested redirect URL against the
    configured trusted origins to prevent open redirect attacks.
    """
    
    # Use a safe default destination to prevent untrusted redirect targets.
    l_safe_redirect_url = "/desk"

    if i_redirect_to_nextjs:
        ld_parsed_url = urlparse(i_redirect_to_nextjs)

        # Restrict redirect destinations to configured frontend origins to prevent open redirect attacks.
        la_configured_cors = frappe.conf.get("allow_cors") or []

        # Normalize configured origins so they can be compared consistently with the requested redirect URL.
        if isinstance(la_configured_cors, str):
            la_allowed_domains = [urlparse(la_configured_cors).netloc] if "http" in la_configured_cors else [la_configured_cors]
        else:
            la_allowed_domains = [urlparse(url).netloc if "http" in url else url for url in la_configured_cors]

        # Accept the redirect only when it belongs to a trusted origin.
        if ld_parsed_url.netloc in la_allowed_domains:
            l_safe_redirect_url = i_redirect_to_nextjs
        state = frappe.generate_hash(length=32)
        frappe.cache.set_value(
			f"lmnas-google:{state}",
			{
				"redirect_to": l_safe_redirect_url,
			},
			expires_in_sec=600,
		)
    # Generate the OAuth initiation URL with our safe destination path
    from frappe.utils.oauth import get_oauth2_authorize_url
    auth_url = get_oauth2_authorize_url("google", redirect_to=f"/api/method/lenscloud.api.integration.google_callback?state={state}")

    return {"auth_url": auth_url}


@frappe.whitelist()
def google_callback(state: str):
    """
    Handles the Google OAuth completion flow after Frappe Social Login.

    Frappe authenticates the user through Google and creates the Frappe session.
    This endpoint generates a short-lived one-time LMNAS login code and redirects
    the user back to LMNAS so it can create its own session without sharing the
    Frappe sid cookie.
    """

    if frappe.session.user == "Guest":
        frappe.throw("Not logged in")

    l_state_key = f"lmnas-google:{state}"

    l_data = frappe.cache.get_value(
        l_state_key,
        expires=True,
    )

    if not l_data:
        frappe.throw("Invalid state")
    
    # Delete the state to prevent it from being reused.
    frappe.cache.delete_value(l_state_key)

    l_redirect_to = l_data["redirect_to"]

    l_code = frappe.generate_hash(length=32)

    frappe.cache.set_value(
        f"lmnas-code:{l_code}",
        {
            "user": frappe.session.user,
        },
        expires_in_sec=60,
    )

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = (
        f"{l_redirect_to}?code={l_code}"
    )

@frappe.whitelist(allow_guest=True)
def exchange_google_code(code: str):
    """
    Exchanges a short-lived one-time Google login code for LMNAS user details.

    The code is generated after successful Google authentication, stored temporarily
    in cache, and can only be consumed once. LMNAS uses this response to create its
    own authenticated session without accessing or copying the LensCloud Frappe session.
    """

    if not code or len(code) > 128:
        frappe.throw(
            "Invalid code.",
            frappe.AuthenticationError,
        )

    l_cache_key = f"lmnas-code:{code}"

    ld_data = frappe.cache.get_value(
        l_cache_key,
        expires=True,
    )

    if not ld_data:
        frappe.throw(
            "Invalid or expired code.",
            frappe.AuthenticationError,
        )

    if isinstance(ld_data, str):
        ld_data = frappe.parse_json(ld_data)

    # Make it single-use
    frappe.cache.delete_value(l_cache_key)

    l_user = ld_data.get("user")

    if not l_user:
        frappe.throw(
            "Invalid code.",
            frappe.AuthenticationError,
        )

    ld_user_doc = frappe.get_doc("User", l_user)

    if not ld_user_doc.enabled:
        frappe.throw(
            "User is disabled.",
            frappe.AuthenticationError,
        )

    return {
        "email": ld_user_doc.email,
        "name": ld_user_doc.full_name,
        "picture": ld_user_doc.user_image,
    }