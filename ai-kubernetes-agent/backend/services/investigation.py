"""Investigation Service - orchestrates all Kubernetes investigation components."""

from datetime import datetime
from typing import Any

from ai.agent import AIError, run_diagnosis
from core.logging import logger
from kubernetes.deployment_inspector import DeploymentInspector
from kubernetes.events_analyzer import EventsAnalyzer
from kubernetes.executor import KubectlExecutor, get_executor
from kubernetes.logs_collector import LogsCollector
from kubernetes.network_inspector import NetworkInspector
from kubernetes.pod_inspector import PodInspector


class InvestigationService:
    """Orchestrate Kubernetes investigation."""

    def __init__(self, executor: KubectlExecutor | None = None):
        self.executor = executor or get_executor()
        self.pod_inspector = PodInspector(self.executor)
        self.logs_collector = LogsCollector(self.executor)
        self.events_analyzer = EventsAnalyzer(self.executor)
        self.deployment_inspector = DeploymentInspector(self.executor)
        self.network_inspector = NetworkInspector(self.executor)

    def investigate(self, namespace: str | None = None, context: str | None = None, run_ai: bool = True) -> dict[str, Any]:
        """Run full investigation."""
        # Switch context if provided
        if context:
            logger.info(f"Switching to Kubernetes context: {context}")
            switch_result = self.executor.use_context(context)
            if "error" in switch_result:
                logger.error(f"Failed to switch context: {switch_result.get('error')}")
                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "namespace": namespace,
                    "context": context,
                    "pods": {"healthy": False, "error": switch_result.get("error")},
                    "logs": {},
                    "events": {"error": switch_result.get("error")},
                    "deployments": {"healthy": False, "error": switch_result.get("error")},
                    "network": {"healthy": True, "error": switch_result.get("error")},
                    "summary": {
                        "total_issues": 0,
                        "critical_issues": [],
                        "overall_healthy": False,
                    },
                    "diagnosis": {
                        "root_cause": "Failed to switch Kubernetes context",
                        "explanation": switch_result.get("error", "Unknown error"),
                        "fix": "Verify the context name exists in your kubeconfig",
                        "kubectl_commands": [f"kubectl config use-context {context}"],
                        "prevention": "Ensure kubeconfig is properly configured",
                        "confidence": 0,
                    },
                }

        logger.info(f"Starting investigation for namespace: {namespace or 'all'}, context: {context or 'current'}")

        # Step 1: Check Pods
        logger.info("Step 1/5: Checking pods...")
        pods_result = self.pod_inspector.inspect(namespace)

        # Step 2: Collect Logs for problematic pods
        logger.info("Step 2/5: Collecting logs...")
        problematic_pods = pods_result.get("problematic_pods", [])
        logs_result = self.logs_collector.collect(problematic_pods)

        # Step 3: Analyze Events
        logger.info("Step 3/5: Analyzing events...")
        events_result = self.events_analyzer.analyze(namespace)

        # Step 4: Inspect Deployments
        logger.info("Step 4/5: Inspecting deployments...")
        deployments_result = self.deployment_inspector.inspect(namespace)

        # Step 5: Check Networking
        logger.info("Step 5/5: Checking networking...")
        network_result = self.network_inspector.inspect(namespace)

        # Compile final result
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "namespace": namespace,
            "context": context,
            "pods": pods_result,
            "logs": logs_result,
            "events": events_result,
            "deployments": deployments_result,
            "network": network_result,
        }

        # Add summary
        result["summary"] = self._generate_summary(result)

        # Step 6: AI Diagnosis (optional)
        if run_ai and result["summary"]["total_issues"] > 0:
            logger.info("Step 6/6: Running AI diagnosis...")
            try:
                diagnosis = run_diagnosis(result)
                result["diagnosis"] = diagnosis
            except AIError as e:
                logger.error(f"AI diagnosis failed: {e}")
                result["diagnosis"] = {
                    "root_cause": "AI diagnosis unavailable",
                    "explanation": str(e),
                    "fix": "Check backend logs for details",
                    "kubectl_commands": [],
                    "prevention": "Configure OpenRouter API key",
                    "confidence": 0,
                }
        elif run_ai:
            logger.info("No issues found, skipping AI diagnosis")
            result["diagnosis"] = {
                "root_cause": "No issues detected",
                "explanation": "All components are healthy",
                "fix": "No action needed",
                "kubectl_commands": [],
                "prevention": "Continue monitoring",
                "confidence": 100,
            }

        logger.info("Investigation complete")
        return result

    def _generate_summary(self, result: dict[str, Any]) -> dict[str, Any]:
        """Generate a summary of findings."""
        pods = result.get("pods", {})
        deployments = result.get("deployments", {})
        events = result.get("events", {})
        network = result.get("network", {})

        total_issues = 0
        critical_issues = []

        # Pod issues
        problematic_pods = pods.get("problematic_pods", [])
        total_issues += len(problematic_pods)
        for pod in problematic_pods:
            critical_issues.append({
                "component": "pod",
                "name": f"{pod.get('namespace')}/{pod.get('name')}",
                "status": pod.get("status"),
                "issues": pod.get("issues", []),
            })

        # Deployment issues
        problematic_deployments = deployments.get("problematic_deployments", [])
        total_issues += len(problematic_deployments)
        for dep in problematic_deployments:
            critical_issues.append({
                "component": "deployment",
                "name": f"{dep.get('namespace')}/{dep.get('name')}",
                "status": dep.get("status"),
                "issues": dep.get("issues", []),
            })

        # Network issues
        problematic_services = network.get("problematic_services", [])
        total_issues += len(problematic_services)
        for svc in problematic_services:
            critical_issues.append({
                "component": "service",
                "name": f"{svc.get('namespace')}/{svc.get('name')}",
                "status": "Unhealthy",
                "issues": svc.get("issues", []),
            })

        # Event issues
        critical_events = events.get("critical_events", [])
        total_issues += len(critical_events)
        for event in critical_events[:5]:  # Top 5 critical events
            obj = event.get("object", {})
            critical_issues.append({
                "component": "event",
                "name": f"{obj.get('namespace')}/{obj.get('kind')}/{obj.get('name')}",
                "status": event.get("reason"),
                "issues": [event.get("message", "")],
            })

        return {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "overall_healthy": total_issues == 0,
        }


def run_investigation(namespace: str | None = None, context: str | None = None, run_ai: bool = True) -> dict[str, Any]:
    """Convenience function to run investigation."""
    service = InvestigationService()
    return service.investigate(namespace, context, run_ai=run_ai)
