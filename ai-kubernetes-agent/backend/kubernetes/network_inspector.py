"""Network Inspector - inspect services, endpoints, and networking."""

from typing import Any

from core.logging import logger
from kubernetes.executor import KubectlExecutor, get_executor


class NetworkInspector:
    """Inspect services, endpoints, and networking issues."""

    def __init__(self, executor: KubectlExecutor | None = None):
        self.executor = executor or get_executor()

    def inspect(self, namespace: str | None = None) -> dict[str, Any]:
        """Inspect services and endpoints."""
        logger.info("Inspecting network...")
        services_data = self.executor.get_services(all_namespaces=namespace is None, namespace=namespace)
        endpoints_data = self.executor.get_endpoints(all_namespaces=namespace is None, namespace=namespace)

        services_error = services_data.get("error")
        endpoints_error = endpoints_data.get("error")

        if services_error:
            logger.error(f"Failed to get services: {services_error}")
        if endpoints_error:
            logger.error(f"Failed to get endpoints: {endpoints_error}")

        services = services_data.get("items", []) if not services_error else []
        endpoints = endpoints_data.get("items", []) if not endpoints_error else []

        return self._analyze_network(services, endpoints)

    def _analyze_network(self, services: list[dict], endpoints: list[dict]) -> dict[str, Any]:
        """Analyze services and endpoints for issues."""
        # Build endpoint lookup by service name
        endpoint_map = {}
        for ep in endpoints:
            metadata = ep.get("metadata", {})
            name = metadata.get("name", "")
            namespace = metadata.get("namespace", "default")
            key = f"{namespace}/{name}"
            subsets = ep.get("subsets", [])
            endpoint_map[key] = subsets

        problematic_services = []
        healthy_services = 0
        total_services = len(services)

        for svc in services:
            svc_info = self._analyze_service(svc, endpoint_map)
            if not svc_info["healthy"]:
                problematic_services.append(svc_info)
            else:
                healthy_services += 1

        return {
            "healthy": len(problematic_services) == 0,
            "total_services": total_services,
            "healthy_services": healthy_services,
            "problematic_services": problematic_services,
            "services_without_endpoints": self._find_services_without_endpoints(services, endpoint_map),
            "headless_services": self._find_headless_services(services),
        }

    def _analyze_service(self, service: dict, endpoint_map: dict) -> dict[str, Any]:
        """Analyze a single service."""
        metadata = service.get("metadata", {})
        spec = service.get("spec", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        svc_type = spec.get("type", "ClusterIP")
        selector = spec.get("selector", {})
        ports = spec.get("ports", [])

        key = f"{namespace}/{name}"
        subsets = endpoint_map.get(key, [])

        svc_info = {
            "name": name,
            "namespace": namespace,
            "type": svc_type,
            "selector": selector,
            "ports": ports,
            "healthy": True,
            "issues": [],
            "endpoint_count": 0,
        }

        # Count endpoints
        endpoint_count = 0
        for subset in subsets:
            endpoint_count += len(subset.get("addresses", []))
        svc_info["endpoint_count"] = endpoint_count

        # Headless service (no clusterIP)
        if spec.get("clusterIP") == "None" or spec.get("clusterIP") == "":
            svc_info["headless"] = True
        else:
            svc_info["headless"] = False

        # Check for missing endpoints
        if not svc_info["headless"] and selector and endpoint_count == 0:
            svc_info["healthy"] = False
            svc_info["issues"].append(
                f"Service has selector but no endpoints: {selector}"
            )

        # Check for selector mismatch (service exists but no pods match)
        if selector and endpoint_count == 0 and not svc_info["headless"]:
            svc_info["issues"].append("Possible selector mismatch - no matching pods")

        # ExternalName service (no endpoints expected)
        if svc_type == "ExternalName":
            svc_info["external_name"] = spec.get("externalName", "")
            # These don't have endpoints, so don't flag as unhealthy

        # LoadBalancer service checks
        if svc_type == "LoadBalancer":
            status = service.get("status", {})
            lb_status = status.get("loadBalancer", {})
            ingress = lb_status.get("ingress", [])
            if not ingress:
                svc_info["issues"].append("LoadBalancer pending - no ingress assigned")

        return svc_info

    def _find_services_without_endpoints(self, services: list[dict], endpoint_map: dict) -> list[dict]:
        """Find services that have selectors but no endpoints."""
        result = []
        for svc in services:
            spec = svc.get("spec", {})
            selector = spec.get("selector", {})
            if not selector:
                continue

            metadata = svc.get("metadata", {})
            name = metadata.get("name", "")
            namespace = metadata.get("namespace", "default")
            key = f"{namespace}/{name}"

            subsets = endpoint_map.get(key, [])
            endpoint_count = sum(len(s.get("addresses", [])) for s in subsets)

            if endpoint_count == 0:
                result.append({
                    "name": name,
                    "namespace": namespace,
                    "selector": selector,
                    "type": spec.get("type", "ClusterIP"),
                })
        return result

    def _find_headless_services(self, services: list[dict]) -> list[dict]:
        """Find headless services."""
        result = []
        for svc in services:
            spec = svc.get("spec", {})
            if spec.get("clusterIP") == "None":
                metadata = svc.get("metadata", {})
                result.append({
                    "name": metadata.get("name", ""),
                    "namespace": metadata.get("namespace", "default"),
                    "selector": spec.get("selector", {}),
                })
        return result


def inspect_network(namespace: str | None = None, executor: KubectlExecutor | None = None) -> dict[str, Any]:
    """Convenience function to inspect network."""
    inspector = NetworkInspector(executor)
    return inspector.inspect(namespace)
