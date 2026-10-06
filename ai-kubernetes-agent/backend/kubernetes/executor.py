"""Kubectl Executor - safely execute kubectl commands."""

import json
import shlex
import subprocess
from typing import Any

from core.logging import logger


class KubectlError(Exception):
    """Custom exception for kubectl failures."""
    def __init__(self, command: str, returncode: int, stdout: str, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(f"kubectl command failed: {command} (exit code: {returncode})")


class KubectlExecutor:
    """Execute kubectl commands safely and return structured output."""

    def __init__(self, kubeconfig: str | None = None, timeout: int = 30):
        self.kubeconfig = kubeconfig
        self.timeout = timeout

    def _build_command(self, args: list[str]) -> list[str]:
        """Build kubectl command with optional kubeconfig."""
        cmd = ["kubectl"]
        if self.kubeconfig:
            cmd.extend(["--kubeconfig", self.kubeconfig])
        cmd.extend(args)
        return cmd

    def run(self, args: list[str], parse_json: bool = True) -> dict[str, Any]:
        """Execute kubectl command and return parsed output."""
        cmd = self._build_command(args)
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        logger.debug(f"Executing: {cmd_str}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            logger.error(f"kubectl timeout: {cmd_str}")
            raise KubectlError(cmd_str, -1, "", f"Timeout after {self.timeout}s") from e
        except FileNotFoundError as e:
            logger.error("kubectl not found in PATH")
            raise KubectlError(cmd_str, -1, "", "kubectl not found") from e

        if result.returncode != 0:
            logger.warning(f"kubectl failed: {cmd_str} | stderr: {result.stderr}")
            if parse_json:
                return {"error": result.stderr.strip(), "raw_output": result.stdout}
            return {"error": result.stderr.strip(), "raw_output": result.stdout}

        output = result.stdout.strip()
        if not output:
            return {}

        if parse_json:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from: {cmd_str}")
                return {"raw_output": output}

        return {"raw_output": output}

    def get_pods(self, all_namespaces: bool = True, namespace: str | None = None) -> dict[str, Any]:
        """Get pods."""
        args = ["get", "pods"]
        if all_namespaces:
            args.append("-A")
        elif namespace:
            args.extend(["-n", namespace])
        args.extend(["-o", "json"])
        return self.run(args)

    def get_pods_wide(self, all_namespaces: bool = True, namespace: str | None = None) -> dict[str, Any]:
        """Get pods with wide output."""
        args = ["get", "pods"]
        if all_namespaces:
            args.append("-A")
        elif namespace:
            args.extend(["-n", namespace])
        args.extend(["-o", "json"])
        return self.run(args)

    def get_events(self, all_namespaces: bool = True, namespace: str | None = None) -> dict[str, Any]:
        """Get events."""
        args = ["get", "events"]
        if all_namespaces:
            args.append("-A")
        elif namespace:
            args.extend(["-n", namespace])
        args.extend(["-o", "json"])
        return self.run(args)

    def get_logs(self, pod_name: str, namespace: str = "default", container: str | None = None,
                 previous: bool = False, tail: int = 100) -> dict[str, Any]:
        """Get pod logs."""
        args = ["logs", pod_name, "-n", namespace, "--tail", str(tail)]
        if container:
            args.extend(["-c", container])
        if previous:
            args.append("-p")
        return self.run(args, parse_json=False)

    def describe_pod(self, pod_name: str, namespace: str = "default") -> dict[str, Any]:
        """Describe a pod."""
        args = ["describe", "pod", pod_name, "-n", namespace, "-o", "json"]
        return self.run(args)

    def get_deployments(self, all_namespaces: bool = True, namespace: str | None = None) -> dict[str, Any]:
        """Get deployments."""
        args = ["get", "deployments"]
        if all_namespaces:
            args.append("-A")
        elif namespace:
            args.extend(["-n", namespace])
        args.extend(["-o", "json"])
        return self.run(args)

    def describe_deployment(self, deployment_name: str, namespace: str = "default") -> dict[str, Any]:
        """Describe a deployment."""
        args = ["describe", "deployment", deployment_name, "-n", namespace, "-o", "json"]
        return self.run(args)

    def get_services(self, all_namespaces: bool = True, namespace: str | None = None) -> dict[str, Any]:
        """Get services."""
        args = ["get", "svc"]
        if all_namespaces:
            args.append("-A")
        elif namespace:
            args.extend(["-n", namespace])
        args.extend(["-o", "json"])
        return self.run(args)

    def get_endpoints(self, all_namespaces: bool = True, namespace: str | None = None) -> dict[str, Any]:
        """Get endpoints."""
        args = ["get", "endpoints"]
        if all_namespaces:
            args.append("-A")
        elif namespace:
            args.extend(["-n", namespace])
        args.extend(["-o", "json"])
        return self.run(args)

    def get_nodes(self) -> dict[str, Any]:
        """Get nodes."""
        args = ["get", "nodes", "-o", "json"]
        return self.run(args)

    def get_clusters(self) -> dict[str, Any]:
        """Get available clusters from kubeconfig."""
        args = ["config", "get-clusters"]
        result = self.run(args, parse_json=False)
        if "raw_output" in result:
            # Skip the "NAME" header line
            lines = result["raw_output"].strip().split("\n")
            clusters = [line.strip() for line in lines[1:] if line.strip() and line.strip() != "NAME"]
            result["raw_output"] = "\n".join(clusters)
        return result

    def get_current_context(self) -> dict[str, Any]:
        """Get current kubeconfig context."""
        args = ["config", "current-context"]
        return self.run(args, parse_json=False)

    def use_context(self, context_name: str) -> dict[str, Any]:
        """Switch kubeconfig context."""
        args = ["config", "use-context", context_name]
        return self.run(args, parse_json=False)


_executor: KubectlExecutor | None = None


def get_executor(kubeconfig: str | None = None) -> KubectlExecutor:
    """Get or create kubectl executor singleton."""
    global _executor
    if _executor is None or kubeconfig is not None:
        _executor = KubectlExecutor(kubeconfig=kubeconfig)
    return _executor
