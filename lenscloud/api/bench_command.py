import json
import re
import time

import frappe
from frappe import _
from frappe.utils import now_datetime

from lenscloud.api.kubernetes_client import KubernetesClientError, sanitize_error
from lenscloud.api.orchestration import (
	CUSTOMER_LABEL,
	PLATFORM_MANAGER_LABEL,
	PLATFORM_MANAGER_VALUE,
	RESOURCE_ID_LABEL,
	RESOURCE_KIND_LABEL,
	create_action_log,
	default_runtime_namespace,
	finish_action_log,
	get_cluster_client,
	get_region_cluster,
	label_value,
	manifest_yaml,
)
from lenscloud.api.policy import environment_policy


BENCH_COMMAND_RESOURCE_KIND = "bench-command"
RUNNER_IMAGE = "ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:eebfa0199c328207b14a949fa6232954a203a3937b1eed4930e9c3ec95b654d6"
VERIFICATION_COMMANDS = {"bench_test.status"}
RUNNER_SUPPORTED_COMMANDS = {
	"maintenance_mode.enable",
	"maintenance_mode.disable",
	"maintenance_mode.status",
	"developer_mode.enable",
	"developer_mode.disable",
	"developer_mode.status",
	"site_config.set",
	"site_config.unset",
	"site_config.get",
	"cors.allowlist.update",
	"cors.allowlist.get",
	"backup.status",
}
SUPPORTED_COMMANDS = VERIFICATION_COMMANDS | RUNNER_SUPPORTED_COMMANDS
RUNNER_PENDING_COMMANDS = {
	"backup.create",
	"restore.preview",
	"restore.execute",
	"restore.status",
	"bench_test.trigger",
	"latp.trigger",
	"latp.status",
}
APPROVED_SITE_CONFIG_KEYS = {"maintenance_mode", "developer_mode", "allow_cors", "server_script_enabled", "client_script_enabled"}
CONTRACTED_COMMANDS = {
	"backup.create",
	"backup.status",
	"restore.preview",
	"restore.execute",
	"restore.status",
	"maintenance_mode.enable",
	"maintenance_mode.disable",
	"maintenance_mode.status",
	"developer_mode.enable",
	"developer_mode.disable",
	"developer_mode.status",
	"site_config.set",
	"site_config.unset",
	"site_config.get",
	"cors.allowlist.update",
	"cors.allowlist.get",
	"bench_test.trigger",
	"bench_test.status",
	"latp.trigger",
	"latp.status",
}
COMMAND_FAMILIES = {command.split(".", 1)[0] for command in CONTRACTED_COMMANDS}
SAFE_ID_PATTERN = re.compile(r"[^a-z0-9-]+")


def safe_name(value):
	value = SAFE_ID_PATTERN.sub("-", str(value or "").lower()).strip("-")
	return value[:52].strip("-") or "bench-command"


def command_family(command):
	return (command or "").split(".", 1)[0]


def command_args(command, args):
	if isinstance(args, str):
		args = json.loads(args or "{}")
	if args is None:
		args = {}
	if not isinstance(args, dict):
		frappe.throw(_("Bench Command args must be a JSON object."))
	if command == "bench_test.status":
		mode = args.get("mode") or "status"
		if mode != "status":
			frappe.throw(_("bench_test.status only accepts mode=status."))
		return {"mode": "status"}
	if command.startswith("maintenance_mode.") or command.startswith("developer_mode."):
		return {}
	if command.startswith("site_config."):
		key = str(args.get("key") or "").strip()
		if key not in APPROVED_SITE_CONFIG_KEYS:
			frappe.throw(_("Site config key {0} is not approved for Bench Command execution.").format(key or "<empty>"))
		if command == "site_config.set":
			if "value" not in args:
				frappe.throw(_("site_config.set requires a scalar value."))
			value = args.get("value")
			if isinstance(value, (dict, list)):
				frappe.throw(_("site_config.set value must be scalar."))
			return {"key": key, "value": value}
		return {"key": key}
	if command == "cors.allowlist.update":
		origins = args.get("origins")
		if isinstance(origins, str):
			origins = [item.strip() for item in origins.splitlines() if item.strip()]
		if not isinstance(origins, list) or not all(isinstance(item, str) for item in origins):
			frappe.throw(_("cors.allowlist.update requires origins as a string list."))
		origins = sorted({item.strip() for item in origins if item.strip()})
		if any(item == "*" for item in origins):
			frappe.throw(_("Wildcard CORS origin is not allowed."))
		return {"origins": origins}
	if command == "cors.allowlist.get":
		return {}
	if command == "backup.status":
		return {}
	return args


def timeout_value(value):
	try:
		timeout = int(value or 60)
	except (TypeError, ValueError):
		frappe.throw(_("Timeout must be a number of seconds."))
	if timeout < 10 or timeout > 300:
		frappe.throw(_("Timeout must be between 10 and 300 seconds."))
	return timeout


def get_approved_runtime_namespace(cluster, namespace):
	row = frappe.db.get_value(
		"Runtime Namespace",
		{"cluster": cluster.name, "namespace": namespace, "approved_for_platform": 1},
		["name", "status", "verification_status"],
		as_dict=True,
	)
	if not row or row.status != "Active" or row.verification_status != "Verified":
		frappe.throw(_("Runtime Namespace {0} is not approved and verified for Platform command Jobs.").format(namespace))
	return row


def validate_site_target(site):
	site_doc = frappe.get_doc("Site", site)
	if not site_doc.bench:
		frappe.throw(_("Site {0} must be linked to a Bench before running a Bench Command.").format(site_doc.name))
	bench = frappe.get_doc("Bench", site_doc.bench)
	if bench.region != site_doc.region:
		frappe.throw(_("Site and Bench Region must match."))
	cluster = get_region_cluster(site_doc.region)
	namespace = bench.kubernetes_namespace or default_runtime_namespace(cluster)
	get_approved_runtime_namespace(cluster, namespace)
	if site_doc.cluster and site_doc.cluster != cluster.name:
		frappe.throw(_("Site Cluster does not match the Region runtime Cluster."))
	if bench.cluster and bench.cluster != cluster.name:
		frappe.throw(_("Bench Cluster does not match the Region runtime Cluster."))
	subscription = None
	policy = None
	if site_doc.subscription:
		subscription = frappe.get_doc("Subscription", site_doc.subscription)
		if subscription.customer != site_doc.customer:
			frappe.throw(_("Site customer does not match Subscription customer."))
		if subscription.status not in {"Approved", "Provisioning", "Active"}:
			frappe.throw(_("Subscription {0} is not approved for runtime command execution.").format(subscription.name))
		if site_doc.environment:
			policy = environment_policy(subscription, site_doc.environment)
	return site_doc, bench, cluster, namespace, subscription, policy


def configured_cors_origins(policy):
	controls = policy.get("site_controls") or {}
	return {item.strip() for item in controls.get("cors_origins") or [] if item.strip()}


def validate_command_policy(command, site_doc, subscription, policy, args):
	if command not in CONTRACTED_COMMANDS:
		frappe.throw(_("Bench Command {0} is not in the Platform allowlist.").format(command))
	if command == "bench_test.status":
		return True
	if command in RUNNER_PENDING_COMMANDS:
		return True
	if not subscription or not policy:
		frappe.throw(_("Command {0} requires a Subscription and Environment policy on the Site.").format(command))
	family = command_family(command)
	controls = policy.get("site_controls") or {}
	if family == "bench_test" and not policy.get("gates", {}).get("bench_test"):
		frappe.throw(_("Bench Test commands are not allowed by the active Site Control Profile."))
	if family == "latp" and not policy.get("gates", {}).get("latp"):
		frappe.throw(_("LATP commands are not allowed by the active Site Control Profile."))
	if family == "developer_mode" and command.endswith(".enable"):
		if policy.get("is_production"):
			frappe.throw(_("Developer mode cannot be enabled for a production Site."))
		if not controls.get("enable_developer_mode"):
			frappe.throw(_("Developer mode is not enabled by the active Site Control Profile."))
	if command.startswith("site_config."):
		key = args.get("key")
		if key == "server_script_enabled" and not controls.get("allow_server_scripts"):
			frappe.throw(_("Server scripts are not allowed by the active Site Control Profile."))
		if key == "client_script_enabled" and not controls.get("allow_client_scripts"):
			frappe.throw(_("Client scripts are not allowed by the active Site Control Profile."))
		if key == "developer_mode" and command == "site_config.set" and int(args.get("value") or 0):
			if policy.get("is_production") or not controls.get("enable_developer_mode"):
				frappe.throw(_("Developer mode site_config cannot be enabled by the active Site Control Profile."))
		if key == "allow_cors" and command == "site_config.set" and controls.get("cors_policy") != "Allowlist":
			frappe.throw(_("CORS is not enabled by the active Site Control Profile."))
	if command == "cors.allowlist.update":
		if controls.get("cors_policy") != "Allowlist":
			frappe.throw(_("CORS allowlist updates are not enabled by the active Site Control Profile."))
		allowed = configured_cors_origins(policy)
		requested = set(args.get("origins") or [])
		if allowed and not requested.issubset(allowed):
			frappe.throw(_("CORS origins must be within the active Site Control Profile allowlist."))
	return True


def command_id(log_name):
	return f"BCMD-{log_name.replace('ORCH-', '')}"


def command_resource_names(log_name):
	base = safe_name(command_id(log_name))
	return f"{base}-request", f"{base}-job"


def metadata_labels(command_id_value, site_doc):
	labels = {
		PLATFORM_MANAGER_LABEL: PLATFORM_MANAGER_VALUE,
		RESOURCE_KIND_LABEL: BENCH_COMMAND_RESOURCE_KIND,
		RESOURCE_ID_LABEL: label_value(command_id_value),
	}
	if site_doc.customer:
		labels[CUSTOMER_LABEL] = label_value(site_doc.customer)
	return labels


def metadata_annotations(command, request_name):
	return {
		"lenscloud.io/bench-command-family": command_family(command),
		"lenscloud.io/bench-command": command,
		"lenscloud.io/bench-command-request": request_name,
	}


def request_document(command_id_value, command, site_doc, bench, cluster, namespace, args, timeout, reason):
	return {
		"apiVersion": "lenscloud.io/v1",
		"kind": "BenchCommand",
		"commandId": command_id_value,
		"command": command,
		"target": {
			"cluster": cluster.name,
			"namespace": namespace,
			"bench": bench.operator_resource_name or bench.name,
			"site": site_doc.name,
		},
		"args": args,
		"timeoutSeconds": timeout,
		"requestedBy": frappe.session.user,
		"reason": sanitize_error(reason or f"Apply Site Control command {command}"),
	}


def configmap_manifest(name, namespace, labels, annotations, request):
	return {
		"apiVersion": "v1",
		"kind": "ConfigMap",
		"metadata": {"name": name, "namespace": namespace, "labels": labels, "annotations": annotations},
		"data": {"request.json": json.dumps(request, sort_keys=True, indent=2)},
	}


def bench_sites_pvc_name(bench):
	return f"{bench.operator_resource_name or bench.name}-sites"


def verification_job_container(labels, command):
	summary = json.dumps({
		"phase": "Succeeded",
		"commandId": labels[RESOURCE_ID_LABEL],
		"command": command,
		"summary": "Bench Test status contract check completed",
		"changed": False,
		"redacted": True,
	}, separators=(",", ":"))
	return {
		"name": "bench-command",
		"image": "busybox:1.36",
		"command": ["sh", "-c", f"printf '%s\n' '{summary}' > /dev/termination-log"],
		"volumeMounts": [{"name": "request", "mountPath": "/request", "readOnly": True}],
	}


def runner_job_container():
	return {
		"name": "bench-command",
		"image": RUNNER_IMAGE,
		"imagePullPolicy": "IfNotPresent",
		"env": [
			{"name": "BENCH_PATH", "value": "/home/frappe/frappe-bench"},
			{"name": "BENCH_COMMAND_REQUEST", "value": "/lenscloud/request/request.json"},
		],
		"command": ["/usr/local/bin/lenscloud-bench-command-runner"],
		"volumeMounts": [
			{"name": "request", "mountPath": "/lenscloud/request", "readOnly": True},
			{"name": "sites", "mountPath": "/home/frappe/frappe-bench/sites"},
		],
	}


def job_manifest(name, namespace, labels, annotations, request_name, command, bench=None):
	volumes = [{"name": "request", "configMap": {"name": request_name}}]
	container = verification_job_container(labels, command)
	if command in RUNNER_SUPPORTED_COMMANDS:
		if not bench:
			frappe.throw(_("Bench is required for runner-backed Bench Commands."))
		volumes.append({"name": "sites", "persistentVolumeClaim": {"claimName": bench_sites_pvc_name(bench)}})
		container = runner_job_container()
	return {
		"apiVersion": "batch/v1",
		"kind": "Job",
		"metadata": {"name": name, "namespace": namespace, "labels": labels, "annotations": annotations},
		"spec": {
			"backoffLimit": 0,
			"template": {
				"metadata": {"labels": labels},
				"spec": {
					"automountServiceAccountToken": False,
					"restartPolicy": "Never",
					"containers": [container],
					"volumes": volumes,
				},
			},
		},
	}


def phase_from_job(job):
	status = job.get("status") or {}
	if status.get("succeeded"):
		return "Succeeded"
	if status.get("failed"):
		return "Failed"
	if status.get("active"):
		return "Running"
	return "Queued"


def sanitized_termination_summary(pods):
	for pod in pods:
		for container in (pod.get("status") or {}).get("containerStatuses") or []:
			terminated = ((container.get("state") or {}).get("terminated") or {})
			message = terminated.get("message")
			if not message:
				continue
			text = sanitize_error(message)
			try:
				return json.loads(text)
			except ValueError:
				return {"phase": "Succeeded" if terminated.get("exitCode") == 0 else "Failed", "summary": text[:500], "redacted": True}
	return None


def pod_phase(pod):
	return ((pod.get("status") or {}).get("phase") or "Unknown")


def is_terminal_pod(pod):
	if pod_phase(pod) in {"Succeeded", "Failed"}:
		return True
	for container in (pod.get("status") or {}).get("containerStatuses") or []:
		state = container.get("state") or {}
		if state.get("terminated"):
			return True
	return False


def pod_name(pod):
	return ((pod.get("metadata") or {}).get("name") or "")


def pod_labels(pod):
	return ((pod.get("metadata") or {}).get("labels") or {})


def is_platform_bench_command_pod(pod):
	labels = pod_labels(pod)
	return labels.get(PLATFORM_MANAGER_LABEL) == PLATFORM_MANAGER_VALUE and labels.get(RESOURCE_KIND_LABEL) == BENCH_COMMAND_RESOURCE_KIND


def delete_terminal_command_pods(client, namespace, pods):
	deleted = []
	unsafe = []
	active = []
	for pod in pods:
		name = pod_name(pod)
		if not name:
			continue
		if not is_platform_bench_command_pod(pod):
			unsafe.append(f"{namespace}/{name}")
			continue
		if not is_terminal_pod(pod):
			active.append(f"{namespace}/{name}:{pod_phase(pod)}")
			continue
		try:
			client.delete_namespaced("pods", namespace, name)
			deleted.append(f"pods/{namespace}/{name}")
		except KubernetesClientError as exc:
			if "Kubernetes API 404:" not in str(exc):
				raise
	if unsafe:
		raise KubernetesClientError(f"Bench Command cleanup refused pod(s) without Platform bench-command labels: {', '.join(unsafe)}")
	if active:
		raise KubernetesClientError(f"Bench Command cleanup refused non-terminal pod(s): {', '.join(active)}")
	return deleted


def cleanup_command_pods(client, namespace, job_name, wait_seconds=20):
	if not job_name:
		return []
	selector = f"job-name={job_name}"
	deadline = time.time() + wait_seconds
	pods = client.list_namespaced("pods", namespace, label_selector=selector)
	while pods and time.time() < deadline and all(is_terminal_pod(pod) for pod in pods):
		time.sleep(2)
		pods = client.list_namespaced("pods", namespace, label_selector=selector)
	deleted = delete_terminal_command_pods(client, namespace, pods)
	remaining = client.list_namespaced("pods", namespace, label_selector=selector)
	remaining_names = [pod_name(pod) for pod in remaining if pod_name(pod)]
	if remaining_names:
		raise KubernetesClientError(f"Bench Command cleanup still sees pod(s) for job {job_name}: {', '.join(remaining_names)}")
	return deleted


def cleanup_terminal_bench_command_pods(cluster, namespace):
	selector = f"{PLATFORM_MANAGER_LABEL}={PLATFORM_MANAGER_VALUE},{RESOURCE_KIND_LABEL}={BENCH_COMMAND_RESOURCE_KIND}"
	with get_cluster_client(cluster) as client:
		pods = client.list_namespaced("pods", namespace, label_selector=selector)
		deleted = delete_terminal_command_pods(client, namespace, pods)
		remaining = client.list_namespaced("pods", namespace, label_selector=selector)
		terminal_remaining = [pod_name(pod) for pod in remaining if pod_name(pod) and is_terminal_pod(pod)]
		if terminal_remaining:
			raise KubernetesClientError(f"Bench Command cleanup still sees terminal pod(s): {', '.join(terminal_remaining)}")
	return deleted


def cleanup_command_resources(cluster, namespace, job_name, request_name, pod_wait_seconds=20):
	deleted = []
	with get_cluster_client(cluster) as client:
		for resource, name, group in (("jobs", job_name, "batch"), ("configmaps", request_name, "")):
			if not name:
				continue
			try:
				client.delete_namespaced(resource, namespace, name, group=group, version="v1")
				deleted.append(f"{resource}/{namespace}/{name}")
			except KubernetesClientError as exc:
				if "Kubernetes API 404:" not in str(exc):
					raise
		deleted.extend(cleanup_command_pods(client, namespace, job_name, wait_seconds=pod_wait_seconds))
	return deleted


def wait_for_job(cluster, namespace, job_name, labels, timeout):
	selector = ",".join(f"{key}={value}" for key, value in labels.items())
	deadline = time.time() + timeout
	last_job = None
	last_pods = []
	with get_cluster_client(cluster) as client:
		while time.time() < deadline:
			last_job = client.get_namespaced("jobs", namespace, job_name, group="batch", version="v1")
			last_pods = client.list_namespaced("pods", namespace, label_selector=selector)
			phase = phase_from_job(last_job)
			if phase in {"Succeeded", "Failed"}:
				return phase, last_job, last_pods
			time.sleep(2)
	return "Timed Out", last_job, last_pods


def sanitize_display_value(value):
	if isinstance(value, dict):
		return {sanitize_error(key): sanitize_display_value(item) for key, item in value.items()}
	if isinstance(value, list):
		return [sanitize_display_value(item) for item in value]
	if isinstance(value, (int, float, bool)) or value is None:
		return value
	return sanitize_error(value)


def safe_command_display(summary):
	if not isinstance(summary, dict):
		return None
	display = summary.get("display")
	if not isinstance(display, dict) or display.get("safe") is not True:
		return None
	label = sanitize_error(display.get("label") or "").strip()
	if not label:
		return None
	value = display.get("value")
	if isinstance(value, list):
		value = ", ".join(sanitize_error(item) for item in value)
	else:
		value = sanitize_error(value)
	kind = sanitize_error(display.get("kind") or "string")
	result = {"label": label, "value": value, "kind": kind, "safe": True}
	if "rawValue" in display:
		result["rawValue"] = sanitize_display_value(display.get("rawValue"))
	return result


def command_display_text(display):
	if not display:
		return None
	value = display.get("value")
	if value in (None, ""):
		return display.get("label")
	return f"{display.get('label')}: {value}"


def sanitized_status_summary(summary):
	if not isinstance(summary, dict):
		return None
	items = []
	for key in ("phase", "code", "summary"):
		value = summary.get(key)
		if value not in (None, ""):
			items.append(f"{key}: {sanitize_error(value)}")
	return "; ".join(items) if items else None


def command_result_next_actions(summary):
	if isinstance(summary, dict):
		code = summary.get("code")
		text = str(summary.get("summary") or "").lower()
		if code == "TARGET_NOT_FOUND" and "site_config.json" in text:
			return [
				"Ask Infra to verify the Bench Command runner mount/path contract for the real Bench sites PVC.",
				"Confirm the runner can see the target Site directory and site_config.json without exposing file contents or Secrets.",
				"Keep backup, restore, Bench Test trigger, and LATP unsupported until runner contracts are complete.",
			]
	return ["Open the action log for the sanitized request/job evidence.", "If cleanup failed, rerun cleanup for the listed Job, ConfigMap, and terminal command pods only."]


def unsupported_response(command, log, site_doc, reason="Production runner is not available for this command."):
	message = f"Bench Command {command} is contracted but unsupported by the current runner/API. {reason}"
	finish_action_log(log, "Unsupported", message)
	return {
		"status": "Unsupported",
		"code": "COMMAND_UNSUPPORTED",
		"command": command,
		"site": site_doc.name,
		"action_log": log.name,
		"message": message,
		"next_actions": [
			"Use bench_test.status for the current positive contract check.",
			"Wait for Infra/operator to publish the production runner for this command.",
			"Do not inject unsupported FrappeSite fields.",
		],
	}


def failure_next_action(exc):
	safe_error = sanitize_error(exc)
	text = safe_error.lower()
	if any(marker in text for marker in ("timed out", "connecttimeout", "connection refused", "max retries exceeded")):
		return (
			"Confirm the Kubernetes API is reachable from the Platform devcontainer and the host-side API authorization "
			"watcher is current, then retry. If the operator network changed, ask Infra to run "
			"`./scripts/52-authorize-platform-api.sh --watch` from the lenscloud-infra host checkout."
		)
	if "cannot delete resource \"pods\"" in text or "cannot delete resource pods" in text:
		return (
			"Ask Infra to add or confirm the INF-010 Bench Command terminal-pod cleanup permission for the "
			"Platform service account in the target Runtime Namespace. Platform already captured the sanitized "
			"command result and deleted the Job/ConfigMap; retry after pod cleanup RBAC/admission is fixed."
		)
	if "403" in text or "forbidden" in text:
		return (
			"Ask Infra to verify INF-010 RBAC/admission for the Platform service account, the target Runtime Namespace, "
			"and the Bench Command Job/ConfigMap/pod cleanup verbs, then retry."
		)
	if "denied" in text or "admission" in text:
		return (
			"Open the action log, compare the generated Job and ConfigMap with the INF-010 admission contract, "
			"correct the rejected shape, then retry."
		)
	return "Open the action log, correct the reported target, namespace, or argument issue, then retry."


@frappe.whitelist()
def run_site_control_command(site, command="bench_test.status", args=None, timeout_seconds=60, reason=None, cleanup=True):
	frappe.only_for("System Manager")
	site_doc, bench, cluster, namespace, subscription, policy = validate_site_target(site)
	args = command_args(command, args)
	timeout = timeout_value(timeout_seconds)
	if command not in CONTRACTED_COMMANDS:
		frappe.throw(_("Bench Command {0} is not in the Platform allowlist.").format(command))
	log = create_action_log(
		"Bench Command",
		"Pending",
		site=site_doc.name,
		bench=bench.name,
		cluster=cluster.name,
		region=site_doc.region,
		dry_run=False,
		resource_kind="bench-command",
		operation=command,
		message=f"Preparing Bench Command {command} for {namespace}/{bench.operator_resource_name or bench.name}/{site_doc.name}.",
	)
	request_name = None
	job_name = None
	try:
		if command not in SUPPORTED_COMMANDS:
			return unsupported_response(command, log, site_doc)
		validate_command_policy(command, site_doc, subscription, policy, args)
		command_id_value = command_id(log.name)
		request_name, job_name = command_resource_names(log.name)
		labels = metadata_labels(command_id_value, site_doc)
		annotations = metadata_annotations(command, request_name)
		request = request_document(command_id_value, command, site_doc, bench, cluster, namespace, args, timeout, reason)
		configmap = configmap_manifest(request_name, namespace, labels, annotations, request)
		job = job_manifest(job_name, namespace, labels, annotations, request_name, command, bench=bench)
		attach_message = {
			"request": request,
			"configMap": {"name": request_name, "namespace": namespace, "labels": labels, "annotations": annotations},
			"job": {"name": job_name, "namespace": namespace, "labels": labels, "annotations": annotations},
		}
		log.manifest = manifest_yaml({"configMap": configmap, "job": job})
		log.message = sanitize_error(json.dumps(attach_message, sort_keys=True, default=str))
		log.status = "Queued"
		log.save(ignore_permissions=True)
		frappe.db.commit()
		with get_cluster_client(cluster) as client:
			client.create_namespaced("configmaps", namespace, configmap)
			client.create_namespaced("jobs", namespace, job, group="batch", version="v1")
		phase, _job, pods = wait_for_job(cluster, namespace, job_name, labels, timeout)
		summary = sanitized_termination_summary(pods)
		deleted = []
		status = phase
		if phase == "Timed Out":
			status = "Failed"
			summary = {"phase": "Timed Out", "code": "TIMEOUT", "summary": "Bench Command Job exceeded Platform timeout.", "redacted": True}
		if cleanup:
			deleted = cleanup_command_resources(cluster, namespace, job_name, request_name)
		display = safe_command_display(summary)
		display_text = command_display_text(display)
		status_text = sanitized_status_summary(summary)
		message = f"Bench Command {command} finished with phase {phase}; cleanup removed {len(deleted)} resource(s)."
		if display_text:
			message = f"{message} Result: {display_text}."
		elif status_text:
			message = f"{message} Summary: {status_text}."
		finish_action_log(log, "Succeeded" if phase == "Succeeded" else "Failed", message)
		return {
			"status": status,
			"command": command,
			"command_id": command_id_value,
			"cluster": cluster.name,
			"namespace": namespace,
			"site": site_doc.name,
			"bench": bench.name,
			"action_log": log.name,
			"request_configmap": request_name,
			"job": job_name,
			"summary": summary,
			"display": display,
			"display_text": display_text,
			"fallback_summary": status_text if not display_text else None,
			"cleanup": deleted,
			"secret_values_returned": False,
			"message": message,
			"next_actions": command_result_next_actions(summary),
		}
	except Exception as exc:
		cleanup_message = ""
		if request_name or job_name:
			try:
				deleted = cleanup_command_resources(cluster, namespace, job_name, request_name)
				cleanup_message = f" Cleanup removed {len(deleted)} temporary resource(s)."
			except Exception as cleanup_exc:
				cleanup_message = f" Cleanup failed: {sanitize_error(cleanup_exc)}."
		finish_action_log(log, "Failed", error=exc, message=f"Bench Command {command} failed.")
		if cleanup_message:
			log.message = f"{log.message}{cleanup_message}"
			log.save(ignore_permissions=True)
		frappe.db.commit()
		safe_error = sanitize_error(exc)
		frappe.throw(_("{0} Action log: {1}. Next action: {2}").format(safe_error, log.name, failure_next_action(exc)))
