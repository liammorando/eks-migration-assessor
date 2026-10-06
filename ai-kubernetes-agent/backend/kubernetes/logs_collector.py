"""Logs Collector - fetch logs for failed pods."""

import re
from typing import Any

from core.logging import logger
from kubernetes.executor import KubectlExecutor, get_executor

ERROR_PATTERNS = [
    (r"(?i)exception", "Exception"),
    (r"(?i)error", "Error"),
    (r"(?i)fail", "Failure"),
    (r"(?i)timeout", "Timeout"),
    (r"(?i)connection refused", "Connection Refused"),
    (r"(?i)connection reset", "Connection Reset"),
    (r"(?i)no such file", "Missing File"),
    (r"(?i)permission denied", "Permission Denied"),
    (r"(?i)out of memory|oom", "Out of Memory"),
    (r"(?i)segmentation fault", "Segmentation Fault"),
    (r"(?i)panic", "Panic"),
    (r"(?i)fatal", "Fatal"),
    (r"(?i)missing.*env", "Missing Environment Variable"),
    (r"(?i)undefined.*variable", "Undefined Variable"),
    (r"(?i)image.*pull", "Image Pull Issue"),
    (r"(?i)crashloop", "CrashLoop"),
    (r"(?i)backoff", "BackOff"),
    (r"(?i)unhealthy", "Unhealthy"),
    (r"(?i)readiness probe failed", "Readiness Probe Failed"),
    (r"(?i)liveness probe failed", "Liveness Probe Failed"),
    (r"(?i)dns", "DNS Issue"),
    (r"(?i)resolve", "Resolution Issue"),
    (r"(?i)certificate", "Certificate Issue"),
    (r"(?i)tls|ssl", "TLS/SSL Issue"),
]


class LogsCollector:
    """Collect and analyze logs from problematic pods."""

    def __init__(self, executor: KubectlExecutor | None = None, tail_lines: int = 200):
        self.executor = executor or get_executor()
        self.tail_lines = tail_lines

    def collect(self, problematic_pods: list[dict[str, Any]]) -> dict[str, Any]:
        """Collect logs for all problematic pods."""
        logger.info(f"Collecting logs for {len(problematic_pods)} problematic pods...")
        results = {}

        for pod in problematic_pods:
            name = pod.get("name")
            namespace = pod.get("namespace", "default")
            key = f"{namespace}/{name}"

            try:
                logs_data = self._collect_pod_logs(name, namespace)
                analysis = self._analyze_logs(logs_data)
                results[key] = {
                    "pod": name,
                    "namespace": namespace,
                    "logs": logs_data,
                    "analysis": analysis,
                }
            except Exception as e:
                logger.error(f"Failed to collect logs for {key}: {e}")
                results[key] = {
                    "pod": name,
                    "namespace": namespace,
                    "error": str(e),
                }

        return results

    def _collect_pod_logs(self, pod_name: str, namespace: str) -> dict[str, Any]:
        """Collect logs from all containers in a pod."""
        # First get pod details to know containers
        pod_details = self.executor.describe_pod(pod_name, namespace)

        containers = []
        if "spec" in pod_details:
            containers = [c.get("name") for c in pod_details["spec"].get("containers", [])]
        if "initContainers" in pod_details.get("spec", {}):
            containers.extend([c.get("name") for c in pod_details["spec"]["initContainers"]])

        logs = {}
        for container in containers:
            try:
                # Get current logs
                result = self.executor.get_logs(pod_name, namespace, container, tail=self.tail_lines)
                logs[container] = result.get("raw_output", "")
            except Exception as e:
                logger.warning(f"Failed to get logs for {pod_name}/{container}: {e}")
                logs[container] = f"Error: {e}"

            # If pod was restarted, also get previous logs
            if "CrashLoopBackOff" in str(pod_details):
                try:
                    result = self.executor.get_logs(
                        pod_name, namespace, container, previous=True, tail=self.tail_lines
                    )
                    logs[f"{container}_previous"] = result.get("raw_output", "")
                except Exception:
                    pass

        return logs

    def _analyze_logs(self, logs: dict[str, str]) -> dict[str, Any]:
        """Analyze logs for error patterns."""
        all_text = " ".join(logs.values())
        findings = []

        for pattern, label in ERROR_PATTERNS:
            matches = list(re.finditer(pattern, all_text, re.IGNORECASE))
            if matches:
                # Get context around first few matches
                contexts = []
                for match in matches[:3]:
                    start = max(0, match.start() - 100)
                    end = min(len(all_text), match.end() + 100)
                    contexts.append(all_text[start:end])

                findings.append({
                    "type": label,
                    "pattern": pattern,
                    "count": len(matches),
                    "contexts": contexts,
                })

        # Also extract last 50 lines as summary
        lines = all_text.split("\n")
        summary = "\n".join(lines[-50:]) if lines else ""

        return {
            "findings": findings,
            "summary": summary,
            "has_errors": len(findings) > 0,
        }


def collect_logs(problematic_pods: list[dict[str, Any]], executor: KubectlExecutor | None = None) -> dict[str, Any]:
    """Convenience function to collect logs."""
    collector = LogsCollector(executor)
    return collector.collect(problematic_pods)
