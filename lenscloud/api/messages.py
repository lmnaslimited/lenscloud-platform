import hashlib
import json
import re

from lenscloud.api.kubernetes_client import sanitize_error


MESSAGE_CATALOG = {
	"LC-PLATFORM-UNKNOWN-0001": ("Platform API", "Platform operation {operation} failed.", "Please retry later or contact support.", "Retry After Platform Action", "Platform"),
	"LC-INFRA-UNKNOWN-0001": ("Infra", "Infrastructure operation {operation} failed with reason {reason}.", "Site setup is waiting for infrastructure recovery.", "Retry After Infra Action", "Infra"),
	"LC-PLATFORM-QUEUE-0001": ("Platform API", "Provisioning queue is overloaded for {operation}.", "Please wait while capacity recovers.", "Retry After Delay", "Platform"),
	"LC-INFRA-RUNNER-0001": ("Runner", "Runner image was rejected for {operation}.", "Site setup is waiting for cluster configuration.", "Retry After Infra Action", "Infra"),
	"LC-INFRA-STORAGE-0001": ("Kubernetes", "Runner storage contract failed for {operation}.", "Site setup is waiting for infrastructure recovery.", "Retry After Infra Action", "Infra"),
	"LC-PLATFORM-BOOTSTRAP-0001": ("Platform API", "Default app installation failed for {site}.", "Please retry after support resolves the app installation issue.", "Retry After Platform Action", "Platform"),
	"LC-INFRA-RUNNER-0002": ("Runner", "Bench command {operation} failed with reason {reason}.", "Please retry after support reviews the failed operation.", "Retry After Infra Action", "Infra"),
}

PATTERNS = (
	("LC-PLATFORM-QUEUE-0001", ("queue overload", "queue is full", "job saturation")),
	("LC-INFRA-RUNNER-0001", ("runner_image_rejected", "approved execution image", "digest mismatch", "not admitted")),
	("LC-INFRA-STORAGE-0001", ("mount failed", "failedmount", "persistentvolumeclaim", "pvc", "subpath")),
	("LC-PLATFORM-BOOTSTRAP-0001", ("default app install failed", "bootstrap app", "site_bootstrap.install_apps")),
	("LC-INFRA-RUNNER-0002", ("runner_failed",)),
)


def safe_params(params):
	clean = {}
	for key, value in (params if isinstance(params, dict) else {"value": params or ""}).items():
		if re.search(r"secret|password|token|credential|private.?key|kubeconfig", str(key), re.I):
			continue
		clean[str(key)] = sanitize_error(value) if isinstance(value, str) else value
	return clean


def resolve_message(message_id=None, operation=None, error=None, params=None, source="Platform API"):
	text = sanitize_error(error or "")
	matched_by = "Infra Supplied" if message_id in MESSAGE_CATALOG else None
	if message_id not in MESSAGE_CATALOG:
		for candidate, markers in PATTERNS:
			if any(marker in text.lower() for marker in markers):
				message_id, matched_by = candidate, "Platform Pattern Match"
				break
	if message_id not in MESSAGE_CATALOG:
		message_id = "LC-INFRA-UNKNOWN-0001" if source in {"Infra", "Runner", "Operator", "Kubernetes"} else "LC-PLATFORM-UNKNOWN-0001"
		matched_by = "Fallback Unknown"
	message_source, template, customer_message, retryability, owner = MESSAGE_CATALOG[message_id]
	values = safe_params({"operation": operation or "unknown", **(params or {})})
	values.setdefault("reason", text or "unknown")
	try:
		operator_message = template.format_map({key: str(value) for key, value in values.items()})
	except KeyError:
		operator_message = template
	stable = {key: value for key, value in values.items() if key not in {"site", "pod", "job", "timestamp", "action_log", "command_id"}}
	signature = hashlib.sha256(json.dumps({"message_id": message_id, "params": stable}, sort_keys=True, default=str).encode()).hexdigest()
	return {
		"message_id": message_id, "message_type": "Error", "source": message_source,
		"destination": "Customer, Platform Operator", "params": values, "normalized_signature": signature,
		"matched_by": matched_by, "match_confidence": 0.8 if matched_by == "Platform Pattern Match" else 0.2 if matched_by == "Fallback Unknown" else 1,
		"customer_message": customer_message, "operator_message": operator_message,
		"resolution_owner": owner, "retryability": retryability,
	}


def attach_message(log, envelope):
	values = {
		"message_id": envelope["message_id"], "message_type": envelope["message_type"], "source": envelope["source"],
		"destination": envelope["destination"], "message_params_json": json.dumps(envelope["params"], sort_keys=True, default=str),
		"normalized_signature": envelope["normalized_signature"], "matched_by": envelope["matched_by"], "match_confidence": envelope["match_confidence"],
		"customer_message": envelope["customer_message"], "operator_message": envelope["operator_message"],
		"resolution_owner": envelope["resolution_owner"], "retryability": envelope["retryability"],
	}
	for field, value in values.items():
		setattr(log, field, value)
	log.save(ignore_permissions=True)
	return log


def emit_message(log, operation=None, error=None, message_id=None, params=None, source="Platform API"):
	envelope = resolve_message(message_id=message_id, operation=operation, error=error, params=params, source=source)
	attach_message(log, envelope)
	return envelope
