import base64
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote

import requests
import yaml


RESOURCE_PATHS = {
	"MariaDB": ("k8s.mariadb.com", "v1alpha1", "mariadbs"),
	"FrappeBench": ("vyogo.tech", "v1", "frappebenches"),
	"FrappeSite": ("vyogo.tech", "v1", "frappesites"),
}
SECRET_PATTERN = re.compile(r"(?i)(token|password|secret|authorization)([\"'=:\s]+)([^\s,}\"]+)")


class KubernetesClientError(RuntimeError):
	pass


def sanitize_error(value):
	text = str(value or "")[:2000]
	return SECRET_PATTERN.sub(r"\1\2[REDACTED]", text)


def kubeconfig_path(reference):
	if not reference or not str(reference).startswith("file:"):
		raise KubernetesClientError("Cluster kubeconfig_reference must use a server-side file: reference.")
	path = Path(str(reference)[5:]).expanduser()
	if not path.is_absolute() or not path.is_file() or not os.access(path, os.R_OK):
		raise KubernetesClientError(f"Restricted kubeconfig is unavailable at {path}.")
	return path


class KubernetesClient:
	def __init__(self, kubeconfig_reference):
		self._temp_files = []
		path = kubeconfig_path(kubeconfig_reference)
		config = yaml.safe_load(path.read_text()) or {}
		context_name = config.get("current-context")
		context = next((item.get("context", {}) for item in config.get("contexts", []) if item.get("name") == context_name), None)
		if not context:
			raise KubernetesClientError("Kubeconfig current context is missing.")
		cluster = next((item.get("cluster", {}) for item in config.get("clusters", []) if item.get("name") == context.get("cluster")), None)
		user = next((item.get("user", {}) for item in config.get("users", []) if item.get("name") == context.get("user")), None)
		if not cluster or not user:
			raise KubernetesClientError("Kubeconfig cluster or user entry is missing.")
		self.server = str(cluster.get("server") or "").rstrip("/")
		if not self.server.startswith("https://"):
			raise KubernetesClientError("Kubernetes API endpoint must use HTTPS.")
		self.namespace = context.get("namespace") or "default"
		self.session = requests.Session()
		self.session.headers.update({"Accept": "application/json"})
		token = user.get("token")
		if not token and user.get("tokenFile"):
			token = Path(user["tokenFile"]).read_text().strip()
		if token:
			self.session.headers["Authorization"] = f"Bearer {token}"
		self.verify = self._certificate_reference(cluster, "certificate-authority", "certificate-authority-data")
		client_cert = self._certificate_reference(user, "client-certificate", "client-certificate-data", required=False)
		client_key = self._certificate_reference(user, "client-key", "client-key-data", required=False)
		self.cert = (client_cert, client_key) if client_cert and client_key else None

	def _certificate_reference(self, entry, path_key, data_key, required=True):
		if entry.get(path_key):
			return entry[path_key]
		if entry.get(data_key):
			content = base64.b64decode(entry[data_key])
			handle = tempfile.NamedTemporaryFile(prefix="lenscloud-kube-", delete=False)
			handle.write(content)
			handle.close()
			os.chmod(handle.name, 0o600)
			self._temp_files.append(handle.name)
			return handle.name
		if required and not entry.get("insecure-skip-tls-verify"):
			raise KubernetesClientError("Kubeconfig has no certificate authority reference.")
		return False if entry.get("insecure-skip-tls-verify") else None

	def close(self):
		self.session.close()
		for path in self._temp_files:
			try:
				os.unlink(path)
			except FileNotFoundError:
				pass

	def __enter__(self):
		return self

	def __exit__(self, *_args):
		self.close()

	def request(self, method, path, **kwargs):
		kwargs.setdefault("timeout", 30)
		kwargs.setdefault("verify", self.verify)
		if self.cert:
			kwargs.setdefault("cert", self.cert)
		try:
			response = self.session.request(method, f"{self.server}{path}", **kwargs)
		except requests.RequestException as exc:
			raise KubernetesClientError(sanitize_error(exc)) from exc
		if response.status_code >= 400:
			raise KubernetesClientError(f"Kubernetes API {response.status_code}: {sanitize_error(response.text)}")
		if not response.content:
			return {}
		return response.json()

	def custom_path(self, kind, namespace, name=None):
		group, version, plural = RESOURCE_PATHS[kind]
		path = f"/apis/{group}/{version}/namespaces/{quote(namespace)}/{plural}"
		return f"{path}/{quote(name)}" if name else path

	def get_custom_resource(self, kind, namespace, name):
		return self.request("GET", self.custom_path(kind, namespace, name))

	def list_custom_resources(self, kind, namespace, label_selector=None):
		params = {"labelSelector": label_selector} if label_selector else None
		return self.request("GET", self.custom_path(kind, namespace), params=params).get("items", [])

	def delete_custom_resource(self, kind, namespace, name):
		return self.request("DELETE", self.custom_path(kind, namespace, name))

	def namespaced_path(self, resource, namespace, name=None, group="", version="v1"):
		if group:
			path = f"/apis/{quote(group)}/{quote(version)}/namespaces/{quote(namespace)}/{quote(resource)}"
		else:
			path = f"/api/{quote(version)}/namespaces/{quote(namespace)}/{quote(resource)}"
		return f"{path}/{quote(name)}" if name else path

	def list_namespaced(self, resource, namespace, label_selector=None, field_selector=None, group="", version="v1"):
		params = {}
		if label_selector:
			params["labelSelector"] = label_selector
		if field_selector:
			params["fieldSelector"] = field_selector
		return self.request("GET", self.namespaced_path(resource, namespace, group=group, version=version), params=params or None).get("items", [])

	def create_namespaced(self, resource, namespace, body, group="", version="v1", dry_run=None):
		params = {"dryRun": dry_run} if dry_run else None
		return self.request("POST", self.namespaced_path(resource, namespace, group=group, version=version), json=body, params=params)

	def delete_namespaced(self, resource, namespace, name, group="", version="v1"):
		return self.request("DELETE", self.namespaced_path(resource, namespace, name, group=group, version=version))

	def get_namespaced(self, resource, namespace, name, group="", version="v1"):
		return self.request("GET", self.namespaced_path(resource, namespace, name, group=group, version=version))

	def apply_custom_resource(self, manifest):
		kind = manifest["kind"]
		metadata = manifest["metadata"]
		path = self.custom_path(kind, metadata["namespace"], metadata["name"])
		return self.request(
			"PATCH",
			path,
			params={"fieldManager": "lenscloud-platform", "force": "true"},
			data=yaml.safe_dump(manifest, sort_keys=False),
			headers={"Content-Type": "application/apply-patch+yaml"},
		)

	def get_secret(self, namespace, name):
		return self.request("GET", f"/api/v1/namespaces/{quote(namespace)}/secrets/{quote(name)}")

	def create_secret(self, namespace, name, string_data, labels=None):
		body = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": name, "namespace": namespace, "labels": labels or {}}, "type": "Opaque", "stringData": string_data}
		return self.request("POST", f"/api/v1/namespaces/{quote(namespace)}/secrets", json=body)

	def can_i(self, verb, group, resource, namespace=None):
		attributes = {"verb": verb, "group": group, "resource": resource}
		if namespace:
			attributes["namespace"] = namespace
		body = {
			"apiVersion": "authorization.k8s.io/v1",
			"kind": "SelfSubjectAccessReview",
			"spec": {"resourceAttributes": attributes},
		}
		result = self.request("POST", "/apis/authorization.k8s.io/v1/selfsubjectaccessreviews", json=body)
		return bool(result.get("status", {}).get("allowed")), result.get("status", {}).get("reason")
