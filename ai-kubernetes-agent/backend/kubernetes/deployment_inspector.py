"""Deployment Inspector - inspect deployments for issues."""

from typing import Any

from core.logging import logger
from kubernetes.executor import KubectlExecutor, get_executor


class DeploymentInspector:
    """Inspect deployments and detect unhealthy ones."""

    def __init__(self, executor: KubectlExecutor | None = None):
        self.executor = executor or get_executor()

    def inspect(self, namespace: str | None = None) -> dict[str, Any]:
        """Inspect all deployments and return health status."""
        logger.info("Inspecting deployments...")
        deployments_data = self.executor.get_deployments(all_namespaces=namespace is None, namespace=namespace)

        if "error" in deployments_data:
            logger.error(f"Failed to get deployments: {deployments_data.get('error')}")
            return {
                "healthy": False,
                "error": deployments_data.get("error"),
                "problematic_deployments": [],
            }

        problematic_deployments = []
        total_deployments = 0
        healthy_deployments = 0

        for item in deployments_data.get("items", []):
            total_deployments += 1
            deployment_info = self._analyze_deployment(item)
            if not deployment_info["healthy"]:
                problematic_deployments.append(deployment_info)
            else:
                healthy_deployments += 1

        return {
            "healthy": len(problematic_deployments) == 0,
            "total_deployments": total_deployments,
            "healthy_deployments": healthy_deployments,
            "problematic_deployments": problematic_deployments,
        }

    def _analyze_deployment(self, deployment: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single deployment for health issues."""
        metadata = deployment.get("metadata", {})
        spec = deployment.get("spec", {})
        status = deployment.get("status", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")

        deployment_info = {
            "name": name,
            "namespace": namespace,
            "healthy": True,
            "issues": [],
            "replicas": {
                "desired": spec.get("replicas", 0),
                "available": status.get("availableReplicas", 0),
                "unavailable": status.get("unavailableReplicas", 0),
                "ready": status.get("readyReplicas", 0),
                "updated": status.get("updatedReplicas", 0),
            },
            "conditions": [],
        }

        # Check replica counts
        desired = deployment_info["replicas"]["desired"]
        available = deployment_info["replicas"]["available"]
        unavailable = deployment_info["replicas"]["unavailable"]

        if unavailable > 0:
            deployment_info["healthy"] = False
            deployment_info["issues"].append(
                f"Unavailable replicas: {unavailable}/{desired}"
            )

        if available < desired:
            deployment_info["healthy"] = False
            deployment_info["issues"].append(
                f"Replicas not ready: {available}/{desired} available"
            )

        # Check conditions
        conditions = status.get("conditions", [])
        for condition in conditions:
            cond_type = condition.get("type", "")
            cond_status = condition.get("status", "")
            cond_reason = condition.get("reason", "")
            cond_message = condition.get("message", "")

            deployment_info["conditions"].append({
                "type": cond_type,
                "status": cond_status,
                "reason": cond_reason,
                "message": cond_message,
            })

            # Check for problematic conditions
            if cond_type == "Available" and cond_status != "True":
                deployment_info["healthy"] = False
                deployment_info["issues"].append(
                    f"Deployment not available: {cond_reason} - {cond_message}"
                )
            elif cond_type == "Progressing" and cond_status != "True":
                deployment_info["healthy"] = False
                deployment_info["issues"].append(
                    f"Deployment not progressing: {cond_reason} - {cond_message}"
                )
            elif cond_type == "ReplicaFailure" and cond_status == "True":
                deployment_info["healthy"] = False
                deployment_info["issues"].append(
                    f"Replica failure: {cond_reason} - {cond_message}"
                )

        # Check rollout status
        observed_generation = status.get("observedGeneration", 0)
        generation = metadata.get("generation", 0)
        if observed_generation < generation:
            deployment_info["healthy"] = False
            deployment_info["issues"].append(
                f"Rollout not complete: observed generation {observed_generation} < {generation}"
            )

        # Determine summary status
        if not deployment_info["healthy"]:
            deployment_info["status"] = self._determine_status(deployment_info["issues"])
        else:
            deployment_info["status"] = "Healthy"

        return deployment_info

    def _determine_status(self, issues: list[str]) -> str:
        """Determine a summary status from issues."""
        issue_text = " ".join(issues)
        if "Unavailable replicas" in issue_text:
            return "Unavailable"
        if "Replicas not ready" in issue_text:
            return "Progressing"
        if "Replica failure" in issue_text:
            return "ReplicaFailure"
        if "Rollout not complete" in issue_text:
            return "RolloutPending"
        return "Unhealthy"


def inspect_deployments(namespace: str | None = None, executor: KubectlExecutor | None = None) -> dict[str, Any]:
    """Convenience function to inspect deployments."""
    inspector = DeploymentInspector(executor)
    return inspector.inspect(namespace)
