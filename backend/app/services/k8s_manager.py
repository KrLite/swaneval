"""Kubernetes cluster management service."""

import logging

import yaml

from app.services.k8s_client import create_apps_v1, create_core_v1

logger = logging.getLogger(__name__)


def _get_k8s_client(kubeconfig_encrypted: str):
    """Create a K8s API client from encrypted kubeconfig."""
    return create_core_v1(kubeconfig_encrypted)


def validate_kubeconfig(kubeconfig_yaml: str) -> dict:
    """Validate kubeconfig, test connectivity, return cluster info."""
    from kubernetes import client

    from app.services.k8s_client import _inline_cert_data

    kubeconfig_dict = yaml.safe_load(kubeconfig_yaml)
    if not kubeconfig_dict or "clusters" not in kubeconfig_dict:
        raise ValueError("Invalid kubeconfig: missing clusters")

    clusters = kubeconfig_dict.get("clusters", [])
    api_server = ""
    if clusters:
        api_server = clusters[0].get("cluster", {}).get("server", "")

    # Test connectivity (inline certs to avoid file path issues)
    try:
        _inline_cert_data(kubeconfig_dict)
        from kubernetes.config import new_client_from_config_dict

        api_client = new_client_from_config_dict(kubeconfig_dict)
        v1 = client.CoreV1Api(api_client=api_client)
        v1.list_namespace(limit=1, _request_timeout=10)
    except Exception as e:
        raise ValueError(f"Failed to connect to cluster: {e}") from e

    return {"api_server_url": api_server}


def probe_cluster_resources(kubeconfig_encrypted: str) -> dict:
    """Probe a cluster for GPU, CPU, memory, and node info."""
    v1 = _get_k8s_client(kubeconfig_encrypted)
    nodes = v1.list_node().items

    total_gpu = 0
    total_cpu = 0
    total_mem = 0
    gpu_type = ""

    for node in nodes:
        alloc = node.status.allocatable or {}
        # GPU
        gpu = int(alloc.get("nvidia.com/gpu", 0))
        total_gpu += gpu
        # CPU (convert from e.g. "8" or "8000m")
        cpu_str = alloc.get("cpu", "0")
        if cpu_str.endswith("m"):
            total_cpu += int(cpu_str[:-1])
        else:
            total_cpu += int(float(cpu_str) * 1000)
        # Memory (convert from e.g. "64Gi")
        mem_str = alloc.get("memory", "0")
        total_mem += _parse_memory(mem_str)
        # GPU type from labels
        if gpu > 0 and not gpu_type:
            labels = node.metadata.labels or {}
            gpu_type = labels.get(
                "nvidia.com/gpu.product",
                labels.get("gpu-type", "Unknown GPU"),
            )

    # Compute GPUs in use by running pods
    gpu_in_use = 0
    try:
        pods = v1.list_pod_for_all_namespaces(
            field_selector="status.phase=Running",
        ).items
        for pod in pods:
            for container in pod.spec.containers or []:
                reqs = (container.resources.requests or {}) if container.resources else {}
                gpu_in_use += int(reqs.get("nvidia.com/gpu", 0))
    except Exception as e:
        from app.errors import ResourceError

        raise ResourceError(
            f"Failed to probe GPU usage (pod listing): {e}. "
            "Cannot determine GPU availability — refusing to report "
            "all GPUs as available."
        ) from e

    gpu_available = max(0, total_gpu - gpu_in_use)

    return {
        "gpu_count": total_gpu,
        "gpu_available": gpu_available,
        "gpu_type": gpu_type,
        "cpu_total_millicores": total_cpu,
        "memory_total_bytes": total_mem,
        "node_count": len(nodes),
    }


def get_cluster_nodes(kubeconfig_encrypted: str) -> list[dict]:
    """Get per-node resource details."""
    v1 = _get_k8s_client(kubeconfig_encrypted)
    nodes = v1.list_node().items
    result = []
    for node in nodes:
        alloc = node.status.allocatable or {}
        labels = node.metadata.labels or {}
        gpu = int(alloc.get("nvidia.com/gpu", 0))
        cpu_str = alloc.get("cpu", "0")
        cpu_m = int(cpu_str[:-1]) if cpu_str.endswith("m") else int(float(cpu_str) * 1000)
        result.append(
            {
                "name": node.metadata.name,
                "gpu_count": gpu,
                "gpu_type": labels.get("nvidia.com/gpu.product", ""),
                "cpu_millicores": cpu_m,
                "memory_bytes": _parse_memory(alloc.get("memory", "0")),
                "status": (
                    "Ready"
                    if any(
                        c.type == "Ready" and c.status == "True"
                        for c in (node.status.conditions or [])
                    )
                    else "NotReady"
                ),
            }
        )
    return result


def verify_dcgm_exporter(
    kubeconfig_encrypted: str, namespace: str = "gpu-operator"
) -> dict:
    """Check whether a DCGM Exporter DaemonSet is running in the target namespace.

    Matches on the canonical label ``app.kubernetes.io/name=dcgm-exporter``
    used by NVIDIA's Helm charts. Returns a dict describing the status so
    callers can surface a warning when GPU metric collection is unavailable.

    Fail-soft: if the API call raises (e.g., RBAC forbidden, network error),
    returns ``{"found": False, "error": "..."}`` rather than bubbling up,
    because DCGM verification should never block cluster registration.
    """
    try:
        apps_v1 = create_apps_v1(kubeconfig_encrypted)
        ds_list = apps_v1.list_namespaced_daemon_set(
            namespace,
            label_selector="app.kubernetes.io/name=dcgm-exporter",
            _request_timeout=10,
        )
    except Exception as e:  # kubernetes client raises ApiException; degrade gracefully
        logger.warning("DCGM verify failed for namespace %s: %s", namespace, e)
        return {
            "found": False,
            "daemonset_name": None,
            "desired": 0,
            "ready": 0,
            "namespace": namespace,
            "error": str(e),
        }

    items = ds_list.items or []
    if not items:
        return {
            "found": False,
            "daemonset_name": None,
            "desired": 0,
            "ready": 0,
            "namespace": namespace,
        }

    ds = items[0]
    desired = ds.status.desired_number_scheduled or 0
    ready = ds.status.number_ready or 0
    return {
        "found": True,
        "daemonset_name": ds.metadata.name,
        "desired": desired,
        "ready": ready,
        "namespace": namespace,
    }


def _parse_memory(mem_str: str) -> int:
    """Parse K8s memory string to bytes."""
    mem_str = str(mem_str)
    units = {
        "Ki": 1024,
        "Mi": 1024**2,
        "Gi": 1024**3,
        "Ti": 1024**4,
        "K": 1000,
        "M": 1000**2,
        "G": 1000**3,
        "T": 1000**4,
    }
    for suffix, multiplier in units.items():
        if mem_str.endswith(suffix):
            return int(float(mem_str[: -len(suffix)]) * multiplier)
    try:
        return int(float(mem_str))
    except (ValueError, OverflowError):
        return 0
