import json
import re
import shlex
import time

import frappe
from frappe import _
from frappe.utils import get_url, now_datetime

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
RUNNER_IMAGE = "ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:0ba81c0f4031d452eab71a463a562d5f07ace308ae87967725dd807e00c97570"
RUNNER_CONTRACT_NAMESPACE = "lenscloud-platform-system"
RUNNER_CONTRACT_CONFIGMAP = "lenscloud-platform-cluster-contract"
RUNNER_CONTRACT_KEY = "bench_command_runner_image"
RUNNER_IMAGE_PATTERN = re.compile(r"^ghcr\.io/lmnaslimited/lenscloud-bench-command-runner@sha256:[0-9a-f]{64}$")
RUNNER_IMAGE_REJECTED_CODE = "BENCH_COMMAND_RUNNER_IMAGE_REJECTED"
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
	"site_setup.status",
	"oauth.status",
	"oauth.configure",
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
	"user.ensure",
	"user.disable",
	"user.roles.set",
	"site_access.status",
}
APPROVED_SITE_CONFIG_KEYS = {"maintenance_mode", "developer_mode", "allow_cors", "server_script_enabled", "client_script_enabled"}
APPROVED_SITE_SETUP_KEYS = {"language", "email", "full_name", "country", "timezone", "currency", "company_name", "company_abbr", "industry", "chart_of_accounts", "fiscal_year_start_date", "fiscal_year_end_date"}
APPROVED_OAUTH_CONFIGURE_KEYS = {
	"provider",
	"provider_name",
	"social_login_provider",
	"enable_social_login",
	"client_id",
	"client_secret_source",
	"base_url",
	"authorize_url",
	"access_token_url",
	"redirect_url",
	"api_endpoint",
	"custom_base_url",
	"allow_local_oauth_http",
	"auth_url_data",
	"sign_ups",
}
REQUIRED_OAUTH_CONFIGURE_KEYS = {
	"provider",
	"provider_name",
	"social_login_provider",
	"enable_social_login",
	"client_id",
	"client_secret_source",
	"base_url",
	"authorize_url",
	"access_token_url",
	"redirect_url",
	"api_endpoint",
	"custom_base_url",
}
OAUTH_SECRET_VOLUME_NAME = "oauth-client-secret"
OAUTH_SECRET_MOUNT_PATH = "/lenscloud/secrets"
OAUTH_CLIENT_SECRET_FILE = f"{OAUTH_SECRET_MOUNT_PATH}/client_secret"
SENSITIVE_ARG_KEY_PATTERN = re.compile(r"(password|passwd|secret|token|private|credential|db_|oauth|client_secret|api_key|keyfile)", re.I)
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
	"site_setup.status",
	"site_setup.complete",
	"oauth.status",
	"oauth.configure",
	"user.ensure",
	"user.disable",
	"user.roles.set",
	"site_access.status",
}
COMMAND_FAMILIES = {command.split(".", 1)[0] for command in CONTRACTED_COMMANDS}
SAFE_ID_PATTERN = re.compile(r"[^a-z0-9-]+")
SAFE_PROVIDER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def safe_name(value):
	value = SAFE_ID_PATTERN.sub("-", str(value or "").lower()).strip("-")
	return value[:52].strip("-") or "bench-command"


def command_family(command):
	return (command or "").split(".", 1)[0]


def clean_scalar_arg(command, key, value, max_length=500):
	if isinstance(value, (dict, list)):
		frappe.throw(_("{0} arg {1} must be scalar.").format(command, key))
	if value is None:
		return ""
	return sanitize_error(str(value).strip())[:max_length]


def clean_oauth_provider(value):
	provider = clean_scalar_arg("oauth", "provider", value, max_length=64).lower()
	if not provider or not SAFE_PROVIDER_PATTERN.match(provider):
		frappe.throw(_("OAuth provider must be a lowercase identifier using letters, numbers, dash, or underscore."))
	return provider


def oauth_status_args(args):
	provider = clean_oauth_provider(args.get("provider") or "lenscloud")
	return {"provider": provider}


def oauth_configure_args(args):
	if "client_secret" in args:
		frappe.throw(_("oauth.configure must not include client_secret in request args; use the mounted Secret contract."))
	unknown = sorted(set(args) - APPROVED_OAUTH_CONFIGURE_KEYS)
	if unknown:
		frappe.throw(_("OAuth configure arg {0} is not approved.").format(", ".join(unknown)))
	missing = sorted(key for key in REQUIRED_OAUTH_CONFIGURE_KEYS if args.get(key) in (None, ""))
	if missing:
		frappe.throw(_("oauth.configure requires {0}.").format(", ".join(missing)))
	if args.get("client_secret_source") != "mounted_file":
		frappe.throw(_("oauth.configure client_secret_source must be mounted_file."))
	provider = clean_oauth_provider(args.get("provider"))
	clean = {"provider": provider, "client_secret_source": "mounted_file"}
	for key in ("provider_name", "social_login_provider", "client_id", "base_url", "authorize_url", "access_token_url", "redirect_url", "api_endpoint", "sign_ups"):
		if key in args:
			clean[key] = clean_scalar_arg("oauth.configure", key, args.get(key), max_length=1000)
	clean["enable_social_login"] = bool(args.get("enable_social_login"))
	clean["custom_base_url"] = bool(args.get("custom_base_url"))
	clean["allow_local_oauth_http"] = bool(args.get("allow_local_oauth_http"))
	auth_url_data = args.get("auth_url_data") or {}
	if not isinstance(auth_url_data, dict):
		frappe.throw(_("oauth.configure auth_url_data must be an object."))
	clean["auth_url_data"] = {
		clean_scalar_arg("oauth.configure", key, key, max_length=60): clean_scalar_arg("oauth.configure", key, value, max_length=500)
		for key, value in auth_url_data.items()
	}
	return clean


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
	if command == "oauth.status":
		return oauth_status_args(args)
	if command == "oauth.configure":
		return oauth_configure_args(args)
	if command == "site_setup.status":
		return {}
	if command == "site_setup.complete":
		clean = {}
		for key, value in args.items():
			key = str(key or "").strip()
			if not key:
				continue
			if SENSITIVE_ARG_KEY_PATTERN.search(key):
				frappe.throw(_("Setup arg {0} is not allowed because it looks sensitive.").format(key))
			if key not in APPROVED_SITE_SETUP_KEYS:
				frappe.throw(_("Setup arg {0} is not approved for Site setup completion.").format(key))
			if isinstance(value, (dict, list)):
				frappe.throw(_("Setup arg {0} must be scalar.").format(key))
			if value not in (None, ""):
				clean[key] = sanitize_error(value)
		for required in ("language", "email", "full_name", "country", "timezone", "currency"):
			if not clean.get(required):
				frappe.throw(_("site_setup.complete requires {0}.").format(required))
		return clean
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
	if family in {"site_setup", "oauth"}:
		return True
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


def secret_manifest(name, namespace, labels, annotations, client_secret):
	if not client_secret:
		frappe.throw(_("OAuth client secret is required for oauth.configure."))
	return {
		"apiVersion": "v1",
		"kind": "Secret",
		"metadata": {"name": name, "namespace": namespace, "labels": labels, "annotations": annotations},
		"type": "Opaque",
		"stringData": {"client_secret": client_secret},
	}


def bench_sites_pvc_name(bench):
	return f"{bench.operator_resource_name or bench.name}-sites"


def validate_runner_image(image):
	image = (image or "").strip()
	if not RUNNER_IMAGE_PATTERN.match(image):
		frappe.throw(_("Bench Command runner image must be the cluster contract ghcr.io/lmnaslimited/lenscloud-bench-command-runner@sha256:<digest>."))
	return image


def bench_command_runner_image(cluster=None):
	if cluster:
		image = getattr(cluster, "bench_command_runner_image", None)
		if image:
			return validate_runner_image(image)
		frappe.throw(_("Cluster {0} has no synced Bench Command runner image. Sync the Cluster runner contract before running Bench Commands.").format(getattr(cluster, "name", "<unknown>")))
	return RUNNER_IMAGE


@frappe.whitelist()
def sync_cluster_bench_command_runner_contract(cluster):
	frappe.only_for("System Manager")
	cluster_doc = frappe.get_doc("Cluster", cluster)
	try:
		with get_cluster_client(cluster_doc) as client:
			configmap = client.get_namespaced("configmaps", RUNNER_CONTRACT_NAMESPACE, RUNNER_CONTRACT_CONFIGMAP)
		image = validate_runner_image(((configmap.get("data") or {}).get(RUNNER_CONTRACT_KEY) or "").strip())
		cluster_doc.bench_command_runner_image = image
		cluster_doc.bench_command_runner_contract_status = "Synced"
		cluster_doc.bench_command_runner_contract_checked_on = now_datetime()
		cluster_doc.bench_command_runner_contract_error = None
		cluster_doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "Synced", "cluster": cluster_doc.name, "bench_command_runner_image": image, "checked_on": cluster_doc.bench_command_runner_contract_checked_on}
	except Exception as exc:
		cluster_doc.bench_command_runner_contract_status = "Failed"
		cluster_doc.bench_command_runner_contract_checked_on = now_datetime()
		cluster_doc.bench_command_runner_contract_error = sanitize_error(exc)
		cluster_doc.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.throw(_("Bench Command runner contract sync failed for Cluster {0}: {1}").format(cluster_doc.name, sanitize_error(exc)))


def is_runner_image_admission_error(exc):
	text = sanitize_error(exc).lower()
	return "approved execution image" in text or RUNNER_IMAGE_REJECTED_CODE.lower() in text


def bench_command_runner_rejected_error(exc, runner_image):
	return KubernetesClientError(
		f"code: {RUNNER_IMAGE_REJECTED_CODE}; operator_message: Bench Command runner image is not admitted by this cluster.; customer_message: Site setup is waiting for cluster configuration. Please retry after support resolves it.; runner_image: {sanitize_error(runner_image)}; admission: {sanitize_error(exc)}"
	)


def dry_run_bench_command_job(client, namespace, job, runner_image):
	try:
		client.create_namespaced("jobs", namespace, job, group="batch", version="v1", dry_run="All")
	except KubernetesClientError as exc:
		if is_runner_image_admission_error(exc):
			raise bench_command_runner_rejected_error(exc, runner_image) from exc
		raise


def runner_contract_validation_job(cluster, namespace, runner_image):
	command = "site_setup.status"
	request_name = f"{safe_name(cluster.name)}-runner-contract-validate-request"
	job_name = f"{safe_name(cluster.name)}-runner-contract-validate-job"
	command_id_value = f"{safe_name(cluster.name)}-runner-contract-validate"
	labels = {
		PLATFORM_MANAGER_LABEL: PLATFORM_MANAGER_VALUE,
		RESOURCE_KIND_LABEL: BENCH_COMMAND_RESOURCE_KIND,
		RESOURCE_ID_LABEL: label_value(command_id_value),
	}
	annotations = metadata_annotations(command, request_name)
	bench = frappe._dict({"name": "runner-contract-validate", "operator_resource_name": "runner-contract-validate"})
	return job_manifest(job_name, namespace, labels, annotations, request_name, command, bench=bench, runner_image=runner_image)


@frappe.whitelist()
def validate_cluster_bench_command_runner_contract(cluster):
	frappe.only_for("System Manager")
	cluster_doc = frappe.get_doc("Cluster", cluster)
	namespace = default_runtime_namespace(cluster_doc)
	try:
		runner_image = bench_command_runner_image(cluster_doc)
		job = runner_contract_validation_job(cluster_doc, namespace, runner_image)
		with get_cluster_client(cluster_doc) as client:
			dry_run_bench_command_job(client, namespace, job, runner_image)
		cluster_doc.bench_command_runner_contract_status = "Synced"
		cluster_doc.bench_command_runner_contract_checked_on = now_datetime()
		cluster_doc.bench_command_runner_contract_error = None
		cluster_doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {
			"status": "Accepted",
			"cluster": cluster_doc.name,
			"runtime_namespace": namespace,
			"command": "site_setup.status",
			"bench_command_runner_image": runner_image,
			"message": "Cluster admission accepted the synced Bench Command runner image for generic runner commands.",
			"next_actions": [
				"Run customer Site setup/status, OAuth, or other generic Bench Commands normally.",
				"If Infra changes the accepted runner digest later, run Sync Bench Runner Contract and then validate again.",
			],
		}
	except Exception as exc:
		cluster_doc.bench_command_runner_contract_status = "Failed"
		cluster_doc.bench_command_runner_contract_checked_on = now_datetime()
		cluster_doc.bench_command_runner_contract_error = sanitize_error(exc)
		cluster_doc.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.throw(_("Bench Command runner contract validation failed for Cluster {0}: {1}").format(cluster_doc.name, sanitize_error(exc)))


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


def runner_job_container(command=None, oauth_secret_name=None, runner_image=None):
	read_only_sites = command in {"site_setup.status", "oauth.status"}
	env = [
		{"name": "BENCH_PATH", "value": "/home/frappe/frappe-bench"},
		{"name": "BENCH_COMMAND_REQUEST", "value": "/lenscloud/request/request.json"},
	]
	volume_mounts = [
		{"name": "request", "mountPath": "/lenscloud/request", "readOnly": True},
		{"name": "sites", "mountPath": "/home/frappe/frappe-bench/sites", "subPath": "frappe-sites", "readOnly": read_only_sites},
	]
	if command == "oauth.configure":
		if not oauth_secret_name:
			frappe.throw(_("oauth.configure requires a short-lived OAuth client Secret mount."))
		env.append({"name": "LENS_COMMAND_OAUTH_CLIENT_SECRET_PATH", "value": OAUTH_CLIENT_SECRET_FILE})
		volume_mounts.append({"name": OAUTH_SECRET_VOLUME_NAME, "mountPath": OAUTH_SECRET_MOUNT_PATH, "readOnly": True})
	return {
		"name": "bench-command",
		"image": runner_image or RUNNER_IMAGE,
		"imagePullPolicy": "IfNotPresent",
		"env": env,
		"command": ["/usr/local/bin/lenscloud-bench-command-runner"],
		"volumeMounts": volume_mounts,
	}


def job_manifest(name, namespace, labels, annotations, request_name, command, bench=None, oauth_secret_name=None, runner_image=None):
	volumes = [{"name": "request", "configMap": {"name": request_name}}]
	container = verification_job_container(labels, command)
	if command in RUNNER_SUPPORTED_COMMANDS:
		if not bench:
			frappe.throw(_("Bench is required for runner-backed Bench Commands."))
		volumes.append({"name": "sites", "persistentVolumeClaim": {"claimName": bench_sites_pvc_name(bench)}})
		if command == "oauth.configure":
			if not oauth_secret_name:
				frappe.throw(_("oauth.configure requires a short-lived OAuth client Secret mount."))
			volumes.append({
				"name": OAUTH_SECRET_VOLUME_NAME,
				"secret": {
					"secretName": oauth_secret_name,
					"items": [{"key": "client_secret", "path": "client_secret"}],
				},
			})
		container = runner_job_container(command, oauth_secret_name=oauth_secret_name, runner_image=runner_image)
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


def sanitize_summary_value(value, key=None):
	if isinstance(value, dict):
		return {item_key: sanitize_summary_value(item, key=item_key) for item_key, item in value.items()}
	if isinstance(value, list):
		return [sanitize_summary_value(item, key=key) for item in value]
	if isinstance(value, str):
		if key == "error_excerpt" and len(value) > 2000:
			return sanitize_error(value[-2000:])
		return sanitize_error(value)
	return value


def sanitized_termination_summary(pods):
	fallback = None
	for pod in pods:
		pod_reason = sanitize_error(((pod.get("status") or {}).get("reason") or "").strip())
		for container in (pod.get("status") or {}).get("containerStatuses") or []:
			terminated = ((container.get("state") or {}).get("terminated") or {})
			if not terminated:
				continue
			message = terminated.get("message")
			if message:
				try:
					return sanitize_summary_value(json.loads(message))
				except ValueError:
					text = sanitize_error(message)
					return {"phase": "Succeeded" if terminated.get("exitCode") == 0 else "Failed", "summary": text[:500], "redacted": True}
			exit_code = terminated.get("exitCode")
			reason = sanitize_error(terminated.get("reason") or pod_reason or "Container terminated")
			fallback = {"phase": "Succeeded" if exit_code == 0 else "Failed", "summary": reason, "exitCode": exit_code, "redacted": True}
	return fallback


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


def cleanup_command_resources(cluster, namespace, job_name, request_name, pod_wait_seconds=20, secret_name=None):
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
		if secret_name:
			try:
				client.delete_namespaced("secrets", namespace, secret_name)
				deleted.append(f"secrets/{namespace}/{secret_name}")
			except KubernetesClientError as exc:
				if "Kubernetes API 404:" not in str(exc):
					raise
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
	for key in ("phase", "code", "summary", "failed_step", "exit_code", "error_excerpt"):
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


def site_access_url(site_doc):
	if site_doc.access_url:
		return str(site_doc.access_url).rstrip("/")
	if site_doc.subdomain and site_doc.domain:
		return f"https://{str(site_doc.subdomain).strip().lower()}.{str(site_doc.domain).strip().lower().strip('.')}"
	frappe.throw(_("Site {0} requires an access URL or subdomain/domain before OAuth configuration.").format(site_doc.name))


def platform_oauth_settings():
	settings = frappe.get_single("Platform Settings")
	provider = clean_oauth_provider(getattr(settings, "oauth_provider", None) or "lenscloud")
	provider_name = clean_scalar_arg("oauth", "provider_name", getattr(settings, "oauth_provider_name", None) or "LensCloud", max_length=120)
	base_url = clean_scalar_arg("oauth", "base_url", getattr(settings, "oauth_base_url", None) or get_url(), max_length=300).rstrip("/")
	if not base_url.startswith("https://") and "localhost" not in base_url:
		frappe.throw(_("Platform OAuth base URL must be HTTPS outside local development."))
	return {"provider": provider, "provider_name": provider_name, "base_url": base_url, "allow_local_oauth_http": bool(getattr(settings, "allow_local_oauth_http", 0))}


def oauth_redirect_url(site_doc, provider):
	return f"{site_access_url(site_doc)}/api/method/frappe.integrations.oauth2_logins.custom/{provider}"


def site_oauth_client_app_name(site_doc):
	prefix = getattr(site_doc, "subdomain", None) or str(site_doc.name).split(".")[0]
	environment = getattr(site_doc, "environment", None) or "Prod"
	return f"{prefix}-{environment}"[:140]


def ensure_oauth_client_customer_roles(doc):
	roles = {getattr(row, "role", None) for row in (getattr(doc, "allowed_roles", None) or [])}
	if "All" not in roles:
		doc.append("allowed_roles", {"role": "All"})


def ensure_platform_oauth_client(site_doc, provider, redirect_url):
	app_name = site_oauth_client_app_name(site_doc)
	existing = frappe.get_all("OAuth Client", filters={"app_name": app_name}, pluck="name", limit=1)
	doc = frappe.get_doc("OAuth Client", existing[0]) if existing else frappe.new_doc("OAuth Client")
	doc.app_name = app_name
	doc.default_redirect_uri = redirect_url
	redirects = [item.strip() for item in (doc.redirect_uris or "").splitlines() if item.strip()]
	if redirect_url not in redirects:
		redirects.append(redirect_url)
	doc.redirect_uris = "\n".join(redirects)
	doc.scopes = doc.scopes or "all openid"
	doc.grant_type = "Authorization Code"
	doc.response_type = "Code"
	doc.skip_authorization = 1
	ensure_oauth_client_customer_roles(doc)
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	client_secret = doc.get("client_secret")
	if not doc.client_id or not client_secret:
		frappe.throw(_("Platform OAuth Client could not produce a client ID and secret."))
	return {"name": doc.name, "client_id": doc.client_id, "client_secret": client_secret, "redirect_url": redirect_url}


def oauth_configure_request_args(site_doc, oauth_client=None):
	settings = platform_oauth_settings()
	provider = settings["provider"]
	redirect_url = oauth_redirect_url(site_doc, provider)
	client = oauth_client or ensure_platform_oauth_client(site_doc, provider, redirect_url)
	return oauth_configure_args({
		"provider": provider,
		"provider_name": settings["provider_name"],
		"social_login_provider": "Custom",
		"enable_social_login": True,
		"client_id": client["client_id"],
		"client_secret_source": "mounted_file",
		"base_url": settings["base_url"],
		"allow_local_oauth_http": settings["allow_local_oauth_http"],
		"authorize_url": "/api/method/frappe.integrations.oauth2.authorize",
		"access_token_url": "/api/method/frappe.integrations.oauth2.get_token",
		"redirect_url": redirect_url,
		"api_endpoint": "/api/method/frappe.integrations.oauth2.openid_profile",
		"custom_base_url": True,
		"auth_url_data": {"response_type": "code", "scope": "openid"},
		"sign_ups": "",
	}) | {"_oauth_client_secret": client["client_secret"], "_oauth_client": client["name"]}


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


def _run_site_control_command(site, command="bench_test.status", args=None, timeout_seconds=60, reason=None, cleanup=True, oauth_client_secret=None, oauth_client_name=None, enforce_permissions=True):
	if enforce_permissions:
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
	secret_name = None
	try:
		if command not in SUPPORTED_COMMANDS:
			return unsupported_response(command, log, site_doc)
		validate_command_policy(command, site_doc, subscription, policy, args)
		command_id_value = command_id(log.name)
		request_name, job_name = command_resource_names(log.name)
		if command == "oauth.configure":
			if not oauth_client_secret:
				frappe.throw(_("oauth.configure requires a server-side OAuth client secret."))
			secret_name = f"{safe_name(command_id_value)}-oauth-secret"
		labels = metadata_labels(command_id_value, site_doc)
		annotations = metadata_annotations(command, request_name)
		runner_image = bench_command_runner_image(cluster) if command in RUNNER_SUPPORTED_COMMANDS else None
		request = request_document(command_id_value, command, site_doc, bench, cluster, namespace, args, timeout, reason)
		configmap = configmap_manifest(request_name, namespace, labels, annotations, request)
		secret = secret_manifest(secret_name, namespace, labels, annotations, oauth_client_secret) if secret_name else None
		job = job_manifest(job_name, namespace, labels, annotations, request_name, command, bench=bench, oauth_secret_name=secret_name, runner_image=runner_image)
		attach_message = {
			"request": request,
			"configMap": {"name": request_name, "namespace": namespace, "labels": labels, "annotations": annotations},
			"job": {"name": job_name, "namespace": namespace, "labels": labels, "annotations": annotations},
		}
		if runner_image:
			attach_message["runner_image"] = runner_image
		manifest_items = {"configMap": configmap, "job": job}
		if secret_name:
			attach_message["secret"] = {"name": secret_name, "namespace": namespace, "labels": labels, "annotations": annotations}
			attach_message["oauthClient"] = {"name": oauth_client_name, "client_id": args.get("client_id"), "secret": "mounted_file"}
			manifest_items["secret"] = {"apiVersion": "v1", "kind": "Secret", "metadata": secret["metadata"], "type": "Opaque", "stringData": {"client_secret": "[REDACTED]"}}
		log.manifest = manifest_yaml(manifest_items)
		log.message = sanitize_error(json.dumps(attach_message, sort_keys=True, default=str))
		log.status = "Queued"
		log.save(ignore_permissions=True)
		frappe.db.commit()
		with get_cluster_client(cluster) as client:
			if runner_image:
				dry_run_bench_command_job(client, namespace, job, runner_image)
			client.create_namespaced("configmaps", namespace, configmap)
			if secret:
				client.create_namespaced("secrets", namespace, secret)
			client.create_namespaced("jobs", namespace, job, group="batch", version="v1")
		phase, _job, pods = wait_for_job(cluster, namespace, job_name, labels, timeout)
		summary = sanitized_termination_summary(pods)
		deleted = []
		status = phase
		if phase == "Timed Out":
			status = "Failed"
			summary = {"phase": "Timed Out", "code": "TIMEOUT", "summary": "Bench Command Job exceeded Platform timeout.", "redacted": True}
		if cleanup:
			deleted = cleanup_command_resources(cluster, namespace, job_name, request_name, secret_name=secret_name)
		display = safe_command_display(summary)
		display_text = command_display_text(display)
		status_text = sanitized_status_summary(summary)
		message = f"Bench Command {command} finished with phase {phase}; cleanup removed {len(deleted)} resource(s)."
		if display_text:
			message = f"{message} Result: {display_text}."
		elif status_text:
			message = f"{message} Summary: {status_text}."
		finish_action_log(log, "Succeeded" if phase == "Succeeded" else "Failed", message, result_message=(summary or {}).get("message"))
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
				deleted = cleanup_command_resources(cluster, namespace, job_name, request_name, secret_name=secret_name)
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


@frappe.whitelist()
def run_site_control_command(site, command="bench_test.status", args=None, timeout_seconds=60, reason=None, cleanup=True):
	if command == "oauth.configure":
		frappe.throw(_("Use Configure OAuth so the client secret stays server-side and is passed only through a short-lived Kubernetes Secret."))
	return _run_site_control_command(site, command=command, args=args, timeout_seconds=timeout_seconds, reason=reason, cleanup=cleanup)


def run_site_setup_command_for_orchestration(site, command="site_setup.status", args=None, timeout_seconds=300, reason=None, cleanup=True):
	if command not in {"site_setup.status", "site_setup.complete"}:
		frappe.throw(_("Only Site setup commands can use the orchestration runner."))
	if command == "site_setup.complete":
		return run_site_setup_complete(site, args=args, timeout_seconds=timeout_seconds, enforce_permissions=False)
	return _run_site_control_command(
		site,
		command=command,
		args=args,
		timeout_seconds=timeout_seconds,
		reason=reason,
		cleanup=cleanup,
		enforce_permissions=False,
	)


def run_site_oauth_status_for_orchestration(site, timeout_seconds=300, reason=None, cleanup=True):
	return _run_site_control_command(
		site,
		command="oauth.status",
		args={"provider": platform_oauth_settings()["provider"]},
		timeout_seconds=timeout_seconds,
		reason=reason or "Check LensCloud Platform OAuth on the target Site",
		cleanup=cleanup,
		enforce_permissions=False,
	)


def configure_site_oauth_for_orchestration(site, timeout_seconds=300, reason=None, cleanup=True):
	site_doc = frappe.get_doc("Site", site)
	args = oauth_configure_request_args(site_doc)
	oauth_client_secret = args.pop("_oauth_client_secret")
	oauth_client_name = args.pop("_oauth_client")
	return _run_site_control_command(
		site,
		command="oauth.configure",
		args=args,
		timeout_seconds=timeout_seconds,
		reason=reason or "Configure LensCloud Platform OAuth on the target Site",
		cleanup=cleanup,
		oauth_client_secret=oauth_client_secret,
		oauth_client_name=oauth_client_name,
		enforce_permissions=False,
	)


@frappe.whitelist()
def configure_site_oauth(site, timeout_seconds=300, reason=None, cleanup=True):
	frappe.only_for("System Manager")
	return configure_site_oauth_for_orchestration(site, timeout_seconds=timeout_seconds, reason=reason, cleanup=cleanup)


APP_AWARE_COMMANDS = {"site_bootstrap.install_apps", "site_app.install", "bench.update", "site_setup.complete"}
APP_AWARE_FAMILIES = {"site_bootstrap", "site_app", "bench", "site_setup"}


def app_aware_timeout_value(value):
	try:
		value = int(value or 900)
	except Exception:
		frappe.throw(_("Timeout must be a number of seconds."))
	if value < 10 or value > 1800:
		frappe.throw(_("App-aware timeout must be between 10 and 1800 seconds."))
	return value


def release_runtime_image(release_name):
	if not release_name:
		frappe.throw(_("Release is required for app-aware runtime-image commands."))
	release = frappe.get_doc("Release", release_name)
	if not release.image_digest:
		frappe.throw(_("Release {0} must have image_digest before app-aware commands can run.").format(release.name))
	release_group = frappe.get_doc("Release Group", release.release_group)
	repository = "/".join(filter(None, [(release_group.registry_url or "").rstrip("/"), (release_group.image_repository or "").lstrip("/")]))
	if not repository:
		frappe.throw(_("Release Group {0} requires registry_url and image_repository.").format(release_group.name))
	digest = str(release.image_digest).strip()
	if digest.startswith("sha256:"):
		digest = digest.split(":", 1)[1]
	if not re.match(r"^[0-9a-f]{64}$", digest):
		frappe.throw(_("Release {0} image_digest must be a sha256 64-hex digest.").format(release.name))
	return f"{repository}@sha256:{digest}", release, release_group


def release_group_install_apps(release_group_name, site_creation=False, requested_apps=None):
	release_group = frappe.get_doc("Release Group", release_group_name)
	allowed = []
	seen = set()
	requested = {str(app).strip() for app in (requested_apps or []) if str(app).strip()}
	for row in release_group.get("included_apps") or []:
		app = str(row.app or "").strip()
		if not app or app.lower() == "frappe":
			continue
		if requested and app not in requested:
			continue
		if site_creation and not row.install_at_site_creation:
			continue
		if app in seen:
			frappe.throw(_("Duplicate app {0} in Release Group {1}.").format(app, release_group.name))
		seen.add(app)
		allowed.append({"app": app, "install_sequence": row.install_sequence})
	missing = sorted(requested - seen) if requested else []
	if missing:
		frappe.throw(_("App(s) not present in Release Group {0}: {1}").format(release_group.name, ", ".join(missing)))
	return [row["app"] for row in sorted(allowed, key=lambda item: (item.get("install_sequence") is None, item.get("install_sequence") or 0, item.get("app") or ""))]


def site_setup_complete_script(site_name, args, summary):
	args_json = json.dumps(args, separators=(",", ":"))
	success_summary = json.dumps(summary, separators=(",", ":"))
	site_arg = shlex.quote(str(site_name))
	setup_py = "\n".join([
		"import json",
		"import frappe",
		"from frappe.desk.page.setup_wizard.setup_wizard import setup_complete",
		"frappe.flags.in_install = True",
		f"args = json.loads({json.dumps(args_json)})",
		"result = setup_complete(args)",
		"print(json.dumps(result, default=str))",
	]) + "\n"
	execute_arg = shlex.quote("exec(open('/tmp/site-setup-complete.py').read())")
	termination = "printf '%s\n' " + shlex.quote(success_summary) + " > /dev/termination-log"
	commands = [
		"set -euo pipefail",
		"out=/tmp/site-setup-complete.out",
		"setup_py=/tmp/site-setup-complete.py",
		"printf '%s\n' " + shlex.quote(setup_py) + " > \"$setup_py\"",
		f"if bench --site {site_arg} execute {execute_arg} >\"$out\" 2>&1; then",
		f"  {termination}",
		"else",
		"  rc=$?",
		"  python3 - \"$rc\" \"$out\" > /dev/termination-log <<'PY'",
		"import json, re, sys",
		"rc, path = int(sys.argv[1]), sys.argv[2]",
		"text = open(path, 'r', errors='replace').read().splitlines()[-120:]",
		"excerpt = '\\n'.join(text)[-1400:]",
		"excerpt = re.sub(r'(?i)(token|password|secret|authorization)([\"\\'=:\\s]+)([^\\s,}\"]+)', r'\\1\\2[REDACTED]', excerpt)",
		"print(json.dumps({'phase': 'Failed', 'command': 'site_setup.complete', 'summary': 'Site setup completion failed', 'exit_code': rc, 'error_excerpt': excerpt, 'redacted': True}))",
		"PY",
		"  exit \"$rc\"",
		"fi",
	]
	return "\n".join(commands) + "\n"


def app_install_script(site_name, apps, summary):
	success_summary = json.dumps(summary, separators=(",", ":"))
	termination = "printf '%s\\n' " + shlex.quote(success_summary) + " > /dev/termination-log"
	if not apps:
		return "set -euo pipefail\n" + termination + "\n"
	commands = [
		"set -euo pipefail",
		"run_step() {",
		"  step=\"$1\"",
		"  shift",
		"  out=\"/tmp/${step}.out\"",
		"  if \"$@\" >\"$out\" 2>&1; then",
		"    return 0",
		"  fi",
		"  rc=$?",
		"  python3 - \"$step\" \"$rc\" \"$out\" > /dev/termination-log <<'PY'",
		"import json, re, sys",
		"step, rc, path = sys.argv[1], int(sys.argv[2]), sys.argv[3]",
		"text = open(path, 'r', errors='replace').read().splitlines()[-40:]",
		"excerpt = '\\n'.join(text)[-2000:]",
		"excerpt = re.sub(r'(?i)(token|password|secret|authorization)([\"\'=:\\s]+)([^\\s,}\"]+)', r'\\1\\2[REDACTED]', excerpt)",
		"print(json.dumps({'phase': 'Failed', 'summary': 'Site bootstrap app install failed', 'failed_step': step, 'exit_code': rc, 'error_excerpt': excerpt, 'redacted': True}))",
		"PY",
		"  exit \"$rc\"",
		"}",
	]
	site_arg = shlex.quote(str(site_name))
	for app in apps:
		app_arg = shlex.quote(str(app))
		commands.append(f"if bench --site {site_arg} list-apps | awk '{{print $1}}' | grep -Fxq {app_arg}; then echo 'Skipping already installed app {app}'; else run_step install-app-{app} bench --site {site_arg} install-app {app_arg}; fi")
	commands.append(termination)
	return "\n".join(commands) + "\n"


def bench_update_script(summary):
	commands = [
		"set -euo pipefail",
		"bench --site all set-config -p maintenance_mode 1",
		"bench --site all set-config -p pause_scheduler 1",
		"bench --site all migrate",
		"bench --site all set-config -p maintenance_mode 0",
		"bench --site all set-config -p pause_scheduler 0",
		"printf '%s\n' '" + json.dumps(summary, separators=(",", ":")) + "' > /dev/termination-log",
	]
	return "\n".join(commands) + "\n"


def release_runtime_tag(release_group, release):
	repository = "/".join(filter(None, [(release_group.registry_url or "").rstrip("/"), (release_group.image_repository or "").lstrip("/")]))
	if not repository or not release.image_tag:
		frappe.throw(_("Release {0} requires registry/repository and image_tag before Bench upgrade readiness can be checked.").format(release.name))
	return f"{repository}:{release.image_tag}"


def frappebench_initialized_image(resource):
	return str(((resource.get("status") or {}).get("initializedImage") or "").strip())


def wait_for_bench_initialized_image(cluster, namespace, bench, expected_image, timeout_seconds=300):
	deadline = time.time() + int(timeout_seconds or 300)
	last_image = ""
	with get_cluster_client(cluster) as client:
		while time.time() < deadline:
			resource = client.get_custom_resource("FrappeBench", namespace, bench.operator_resource_name or bench.name)
			last_image = frappebench_initialized_image(resource)
			if last_image == expected_image:
				return {"initialized_image": last_image, "expected_image": expected_image}
			time.sleep(5)
	frappe.throw(_("FrappeBench assets were not initialized for {0}. Last initializedImage: {1}").format(expected_image, last_image or "<empty>"))


def verify_bench_site_assets(bench_name, timeout=15):
	from lenscloud.api.orchestration import check_site_route
	sites = frappe.get_all(
		"Site",
		filters={"bench": bench_name, "site_status": ["not in", ["Deleted", "Deletion Requested", "Deleting"]]},
		fields=["name", "access_url"],
		order_by="modified desc",
		limit=3,
	)
	results = []
	for site in sites:
		result = check_site_route(site, timeout=timeout, strict_asset=True)
		results.append({"site": site.name, "route": result})
	return results


def app_aware_job_manifest(name, namespace, labels, annotations, image, script, bench):
	return {
		"apiVersion": "batch/v1",
		"kind": "Job",
		"metadata": {"name": name, "namespace": namespace, "labels": labels, "annotations": annotations},
		"spec": {
			"backoffLimit": 1,
			"template": {
				"metadata": {"labels": labels},
				"spec": {
					"automountServiceAccountToken": False,
					"restartPolicy": "Never",
					"containers": [{
						"name": "bench-command",
						"image": image,
						"imagePullPolicy": "IfNotPresent",
						"command": ["bash", "-lc"],
						"args": [script],
						"securityContext": {"privileged": False},
						"volumeMounts": [
							{"name": "sites", "mountPath": "/home/frappe/frappe-bench/sites", "subPath": "frappe-sites", "readOnly": False},
							{"name": "sites-assets", "mountPath": "/home/frappe/frappe-bench/sites/assets", "subPath": "frappe-sites/assets", "readOnly": False},
						],
					}],
					"volumes": [
						{"name": "sites", "persistentVolumeClaim": {"claimName": bench_sites_pvc_name(bench)}},
						{"name": "sites-assets", "persistentVolumeClaim": {"claimName": bench_sites_pvc_name(bench)}},
					],
				},
			},
		},
	}


def app_aware_labels(command_id_value, site_doc=None, bench=None):
	labels = {
		PLATFORM_MANAGER_LABEL: PLATFORM_MANAGER_VALUE,
		RESOURCE_KIND_LABEL: BENCH_COMMAND_RESOURCE_KIND,
		RESOURCE_ID_LABEL: label_value(command_id_value),
	}
	customer = getattr(site_doc, "customer", None) or getattr(bench, "owner_customer", None)
	if customer:
		labels[CUSTOMER_LABEL] = label_value(customer)
	return labels


def run_app_aware_job(command, cluster, namespace, bench, image, script, site_doc=None, timeout_seconds=900, message=None):
	if command not in APP_AWARE_COMMANDS:
		frappe.throw(_("Unsupported app-aware command {0}.").format(command))
	log = create_action_log(
		"Bench Command",
		"Pending",
		site=getattr(site_doc, "name", None),
		bench=bench.name,
		cluster=cluster.name,
		region=getattr(site_doc, "region", None) or bench.region,
		dry_run=False,
		resource_kind="bench-command",
		operation=command,
		message=message or f"Preparing app-aware command {command}.",
	)
	job_name = None
	try:
		command_id_value = command_id(log.name)
		job_name = f"{safe_name(command_id_value)}-job"
		labels = app_aware_labels(command_id_value, site_doc=site_doc, bench=bench)
		annotations = {
			"lenscloud.io/bench-command-family": command_family(command),
			"lenscloud.io/bench-command": command,
		}
		job = app_aware_job_manifest(job_name, namespace, labels, annotations, image, script, bench)
		log.manifest = manifest_yaml({"job": job})
		log.message = sanitize_error(json.dumps({"job": job_name, "namespace": namespace, "command": command, "image": image}, sort_keys=True))
		log.status = "Queued"
		log.save(ignore_permissions=True)
		frappe.db.commit()
		with get_cluster_client(cluster) as client:
			client.create_namespaced("jobs", namespace, job, group="batch", version="v1")
		phase, _job, pods = wait_for_job(cluster, namespace, job_name, labels, app_aware_timeout_value(timeout_seconds))
		summary = sanitized_termination_summary(pods) or {"phase": phase, "summary": f"{command} finished with {phase}", "redacted": True}
		deleted = cleanup_command_resources(cluster, namespace, job_name, None)
		message = f"App-aware command {command} finished with phase {phase}; cleanup removed {len(deleted)} resource(s)."
		status = "Succeeded" if phase == "Succeeded" else "Failed"
		error = None if status == "Succeeded" else (sanitized_status_summary(summary) or message)
		finish_action_log(log, status, message, error=error, result_message=(summary or {}).get("message"))
		return {"status": phase, "command": command, "cluster": cluster.name, "namespace": namespace, "bench": bench.name, "site": getattr(site_doc, "name", None), "job": job_name, "action_log": log.name, "summary": summary, "cleanup": deleted, "message": message, "fallback_summary": error if status != "Succeeded" else None}
	except Exception as exc:
		if job_name:
			try:
				cleanup_command_resources(cluster, namespace, job_name, None)
			except Exception:
				pass
		finish_action_log(log, "Failed", error=exc, message=f"App-aware command {command} failed.")
		frappe.db.commit()
		frappe.throw(_("{0} Action log: {1}.").format(sanitize_error(exc), log.name))


@frappe.whitelist()
def run_site_setup_complete(site, args=None, timeout_seconds=900, enforce_permissions=True):
	if enforce_permissions:
		frappe.only_for("System Manager")
	site_doc, bench, cluster, namespace, _subscription, _policy = validate_site_target(site)
	clean_args = command_args("site_setup.complete", args)
	image, _release, _release_group = release_runtime_image(bench.current_release)
	summary = {"phase": "Succeeded", "command": "site_setup.complete", "summary": "Site setup completion succeeded", "site": site_doc.name, "redacted": True}
	script = site_setup_complete_script(site_doc.name, clean_args, summary)
	return run_app_aware_job("site_setup.complete", cluster, namespace, bench, image, script, site_doc=site_doc, timeout_seconds=timeout_seconds, message=f"Complete setup for Site {site_doc.name} using the Release runtime image.")


@frappe.whitelist()
def install_site_bootstrap_apps(site, timeout_seconds=900, enforce_permissions=True):
	if enforce_permissions:
		frappe.only_for("System Manager")
	site_doc, bench, cluster, namespace, _subscription, _policy = validate_site_target(site)
	image, release, release_group = release_runtime_image(bench.current_release)
	apps = release_group_install_apps(release_group.name, site_creation=True)
	summary = {"phase": "Succeeded", "summary": "Site bootstrap app install completed", "apps": apps, "site": site_doc.name, "redacted": True}
	script = app_install_script(site_doc.name, apps, summary)
	return run_app_aware_job("site_bootstrap.install_apps", cluster, namespace, bench, image, script, site_doc=site_doc, timeout_seconds=timeout_seconds, message=f"Install bootstrap apps for Site {site_doc.name}.")


@frappe.whitelist()
def install_site_capability(site, subscription_capability, timeout_seconds=900):
	frappe.only_for("System Manager")
	from lenscloud.api.capability import capability_app_rows, upsert_site_capability_state

	site_doc, bench, cluster, namespace, _subscription, _policy = validate_site_target(site)
	subcap = frappe.get_doc("Subscription Capability", subscription_capability)
	if subcap.subscription != site_doc.subscription:
		frappe.throw(_("Subscription Capability does not belong to the Site Subscription."))
	image, _release, release_group = release_runtime_image(bench.current_release)
	capability_apps = [row["app"] for row in capability_app_rows(subcap.capability) if row.get("install_scope") == "Site"]
	apps = release_group_install_apps(release_group.name, requested_apps=capability_apps)
	upsert_site_capability_state(site_doc, subcap, status="Installing", source="Capability Fulfillment")
	summary = {"phase": "Succeeded", "summary": "Site capability install completed", "capability": subcap.capability, "apps": apps, "site": site_doc.name, "redacted": True}
	script = app_install_script(site_doc.name, apps, summary)
	result = run_app_aware_job("site_app.install", cluster, namespace, bench, image, script, site_doc=site_doc, timeout_seconds=timeout_seconds, message=f"Install capability {subcap.capability} for Site {site_doc.name}.")
	if result.get("status") == "Succeeded":
		subcap.status = "Active"
		subcap.activated_on = now_datetime()
		subcap.last_fulfilled_on = now_datetime()
		subcap.last_action_log = result.get("action_log")
		subcap.save(ignore_permissions=True)
		upsert_site_capability_state(site_doc, subcap, status="Active", source="Command Result", installed_apps=apps)
		frappe.db.commit()
	return result


def bench_update_ready_sites(bench_name):
	sites = frappe.get_all("Site", filters={"bench": bench_name, "site_status": ["not in", ["Deleted", "Deletion Requested", "Deleting"]]}, fields=["name", "upgrade_state", "upgrade_tested", "tested_on", "tested_by"])
	blocked = []
	for site in sites:
		if site.upgrade_state != "Scheduled" or not site.upgrade_tested or not site.tested_on or not site.tested_by:
			blocked.append(site.name)
	return sites, blocked


@frappe.whitelist()
def run_bench_update(bench, timeout_seconds=1800):
	frappe.only_for("System Manager")
	bench_doc = frappe.get_doc("Bench", bench)
	if not bench_doc.next_release:
		frappe.throw(_("Bench {0} requires next_release before update.").format(bench_doc.name))
	current_group = frappe.db.get_value("Release", bench_doc.current_release, "release_group") if bench_doc.current_release else bench_doc.release_group
	next_group = frappe.db.get_value("Release", bench_doc.next_release, "release_group")
	if next_group != bench_doc.release_group or current_group != bench_doc.release_group:
		frappe.throw(_("Bench update target Release must belong to the Bench Release Group."))
	_sites, blocked = bench_update_ready_sites(bench_doc.name)
	if blocked:
		frappe.throw(_("Every active Site must be Scheduled and tested before Bench update. Blocked: {0}").format(", ".join(blocked)))
	cluster = get_region_cluster(bench_doc.region)
	namespace = default_runtime_namespace(cluster)
	if bench_doc.kubernetes_namespace:
		namespace = frappe.db.get_value("Runtime Namespace", bench_doc.kubernetes_namespace, "namespace") or namespace
	image, release, release_group = release_runtime_image(bench_doc.next_release)
	expected_initialized_image = release_runtime_tag(release_group, release)
	summary = {"phase": "Succeeded", "summary": "Bench update completed", "target_release": release.name, "operation": "bench --site all maintenance/pause/migrate", "redacted": True}
	result = run_app_aware_job("bench.update", cluster, namespace, bench_doc, image, bench_update_script(summary), timeout_seconds=timeout_seconds, message=f"Update Bench {bench_doc.name} to {release.name}.")
	if result.get("status") == "Succeeded":
		bench_doc.current_release = bench_doc.next_release
		bench_doc.next_release = None
		bench_doc.upgrade_sop_status = "Runtime Reconciling"
		bench_doc.bench_status = "Updating"
		bench_doc.save(ignore_permissions=True)
		from lenscloud.api.orchestration import reconcile_bench
		reconcile_bench(bench_doc.name, dry_run=False)
		initialized = wait_for_bench_initialized_image(cluster, namespace, bench_doc, expected_initialized_image)
		assets = verify_bench_site_assets(bench_doc.name)
		bench_doc.upgrade_sop_status = "Completed"
		bench_doc.bench_status = "Ready"
		bench_doc.save(ignore_permissions=True)
		result["initialized_image"] = initialized
		result["asset_checks"] = assets
		frappe.db.commit()
	return result
