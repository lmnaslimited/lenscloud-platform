# LensCloud Operator SOPs

- [Platform test cluster handoff](./platform-test-cluster-handoff.md): register a fresh Infra-built test cluster, configure Platform Settings/Region/Cluster/Release data, run validation gates, enable controlled live apply, and operate lifecycle scenarios.
- [Platform lifecycle acceptance](./platform-lifecycle-acceptance.md): manually test Platform and customer creation, runtime inspection, policy rejection, deletion, retry, HTTPS, evidence, and cleanup.

These procedures operate LensCloud through its Platform/customer workspaces and server-side Python Kubernetes API. They never require `kubectl` inside the Platform devcontainer.
