import hashlib
import json

from lenscloud.api.kubernetes_client import sanitize_error
from lenscloud.api.messages import safe_params


INFRA_MESSAGE_CATALOG = {
	"LC-INFRA-RUNNER-0001": ("Runner image digest was rejected or is stale.", "Site setup is waiting for cluster configuration."),
	"LC-INFRA-RUNNER-0002": ("Runner command failed.", "Please retry after support reviews the failed operation."),
	"LC-INFRA-STORAGE-0001": ("Bench sites storage contract is unavailable.", "Site setup is waiting for infrastructure recovery."),
	"LC-INFRA-UNKNOWN-0001": ("Infra command failed with an unknown safe fallback.", "Site setup is waiting for infrastructure recovery."),
	"LC-INFRA-QUEUE-0001": ("Target runtime background jobs did not drain in time.", "Site setup is waiting for runtime capacity to recover."),
	"LC-INFRA-BOOTSTRAP-0001": ("Bootstrap app installation failed.", "Please retry after support resolves the app installation issue."),
	"LC-INFRA-TIMEOUT-0001": ("Runner command timed out.", "Site setup is taking longer than expected. Support can safely review and retry it."),
	"LC-INFRA-COMMAND-0001": ("Runner command is unsupported.", "Site setup is waiting for a supported infrastructure command path."),
}


def resolve_infra_message(result_message, operation=None):
	if not isinstance(result_message, dict):
		return None
	message_id = result_message.get("message_id")
	if message_id not in INFRA_MESSAGE_CATALOG:
		return None
	params = safe_params(result_message.get("params") or {})
	params.setdefault("operation", operation or "unknown")
	safe_summary, customer_message = INFRA_MESSAGE_CATALOG[message_id]
	safe_summary = sanitize_error(result_message.get("safe_summary") or safe_summary)
	stable = {key: value for key, value in params.items() if key not in {"site", "pod", "job", "timestamp", "action_log", "command_id"}}
	signature = hashlib.sha256(json.dumps({"message_id": message_id, "params": stable}, sort_keys=True, default=str).encode()).hexdigest()
	return {
		"message_id": message_id,
		"message_type": result_message.get("message_type") or "Error",
		"source": result_message.get("source") or "Runner",
		"destination": result_message.get("destination") or "Platform",
		"params": params,
		"normalized_signature": signature,
		"matched_by": "Infra Supplied",
		"match_confidence": 1,
		"customer_message": customer_message,
		"operator_message": safe_summary,
		"safe_summary": safe_summary,
		"details_ref": sanitize_error(result_message.get("details_ref")) if result_message.get("details_ref") else None,
		"resolution_owner": "Infra",
		"retryability": "Retry After Infra Action",
	}


def attach_infra_message(log, result_message, operation=None):
	envelope = resolve_infra_message(result_message, operation=operation)
	if not envelope:
		return None
	values = {
		"message_id": envelope["message_id"], "message_type": envelope["message_type"],
		"source": envelope["source"], "destination": envelope["destination"],
		"message_params_json": json.dumps(envelope["params"], sort_keys=True, default=str),
		"normalized_signature": envelope["normalized_signature"], "matched_by": envelope["matched_by"],
		"match_confidence": envelope["match_confidence"], "customer_message": envelope["customer_message"],
		"operator_message": envelope["operator_message"], "safe_summary": envelope["safe_summary"],
		"details_ref": envelope["details_ref"], "resolution_owner": envelope["resolution_owner"],
		"retryability": envelope["retryability"],
	}
	for field, value in values.items():
		setattr(log, field, value)
	log.save(ignore_permissions=True)
	return envelope
