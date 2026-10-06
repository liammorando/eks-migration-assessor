"""Pod Inspector - detect unhealthy pods."""

from typing import Any

from core.logging import logger
from kubernetes.executor import KubectlExecutor, get_executor

UNHEALTHY_PHASES = {
    "Failed",
    "Unknown",
}

UNHEALTHY_CONTAINER_STATES = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerConfigError",
    "CreateContainerError",
    "StartError",
    "OOMKilled",
    "Error",
    "Completed",  # for jobs that failed
}

PENDING_REASONS = {
    "ContainerCreating",
    "PodInitializing",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerConfigError",
    "CreateContainerError",
}


class PodInspector:
    """Inspect pods and detect unhealthy ones."""

    def __init__(self, executor: KubectlExecutor | None = None):
        self.executor = executor or get_executor()

    def inspect(self, namespace: str | None = None) -> dict[str, Any]:
        """Inspect all pods and return health status."""
        logger.info("Inspecting pods...")
        pods_data = self.executor.get_pods(all_namespaces=namespace is None, namespace=namespace)

        if "error" in pods_data:
            logger.error(f"Failed to get pods: {pods_data.get('error')}")
            return {
                "healthy": False,
                "error": pods_data.get("error"),
                "problematic_pods": [],
            }

        problematic_pods = []
        total_pods = 0
        healthy_pods = 0

        for item in pods_data.get("items", []):
            total_pods += 1
            pod_info = self._analyze_pod(item)
            if not pod_info["healthy"]:
                problematic_pods.append(pod_info)
            else:
                healthy_pods += 1

        return {
            "healthy": len(problematic_pods) == 0,
            "total_pods": total_pods,
            "healthy_pods": healthy_pods,
            "problematic_pods": problematic_pods,
        }

    def _analyze_pod(self, pod: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single pod for health issues."""
        metadata = pod.get("metadata", {})
        status = pod.get("status", {})
        spec = pod.get("spec", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        phase = status.get("phase", "Unknown")

        pod_info = {
            "name": name,
            "namespace": namespace,
            "phase": phase,
            "healthy": True,
            "issues": [],
        }

        # Check pod phase
        if phase in UNHEALTHY_PHASES:
            pod_info["healthy"] = False
            pod_info["issues"].append(f"Pod phase: {phase}")

        # Check container statuses
        container_statuses = status.get("containerStatuses", []) or []
        init_container_statuses = status.get("initContainerStatuses", []) or []

        all_containers = container_statuses + init_container_statuses

        for container in all_containers:
            container_name = container.get("name", "unknown")
            state = container.get("state", {})
            waiting = state.get("waiting", {})
            terminated = state.get("terminated", {})
            running = state.get("running", {})

            # Check waiting state
            if waiting:
                reason = waiting.get("reason", "")
                message = waiting.get("message", "")
                if reason in UNHEALTHY_CONTAINER_STATES:
                    pod_info["healthy"] = False
                    pod_info["issues"].append(
                        f"Container '{container_name}': {reason} - {message}"
                    )
                elif reason in PENDING_REASONS:
                    pod_info["healthy"] = False
                    pod_info["issues"].append(
                        f"Container '{container_name}' stuck: {reason} - {message}"
                    )

            # Check terminated state
            if terminated:
                exit_code = terminated.get("exitCode", 0)
                reason = terminated.get("reason", "")
                if exit_code != 0:
                    pod_info["healthy"] = False
                    pod_info["issues"].append(
                        f"Container '{container_name}' terminated: exitCode={exit_code}, reason={reason}"
                    )

            # Check restarts
            restart_count = container.get("restartCount", 0)
            if restart_count > 5:
                pod_info["healthy"] = False
                pod_info["issues"].append(
                    f"Container '{container_name}' high restart count: {restart_count}"
                )

        # Check conditions
        conditions = status.get("conditions", [])
        for condition in conditions:
            if condition.get("type") == "Ready" and condition.get("status") != "True":
                pod_info["healthy"] = False
                pod_info["issues"].append(f"Pod not ready: {condition.get('message', '')}")

        # Determine overall status for summary
        if not pod_info["healthy"]:
            pod_info["status"] = self._determine_status(pod_info["issues"])
        else:
            pod_info["status"] = "Running"

        return pod_info

    def _determine_status(self, issues: list[str]) -> str:
        """Determine a summary status from issues."""
        issue_text = " ".join(issues)
        if "CrashLoopBackOff" in issue_text:
            return "CrashLoopBackOff"
        if "ImagePullBackOff" in issue_text or "ErrImagePull" in issue_text:
            return "ImagePullBackOff"
        if "OOMKilled" in issue_text:
            return "OOMKilled"
        if "Pending" in issue_text or "ContainerCreating" in issue_text:
            return "Pending"
        if "Error" in issue_text:
            return "Error"
        return "Unhealthy"


def inspect_pods(namespace: str | None = None, executor: KubectlExecutor | None = None) -> dict[str, Any]:
    """Convenience function to inspect pods."""
    inspector = PodInspector(executor)
    return inspector.inspect(namespace)
