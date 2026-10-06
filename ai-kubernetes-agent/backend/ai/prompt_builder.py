"""Prompt Builder for Kubernetes troubleshooting."""

from typing import Any

SYSTEM_PROMPT = """You are a Senior Kubernetes Site Reliability Engineer (SRE) with 10+ years of experience troubleshooting production Kubernetes clusters. You have deep expertise in:

- Kubernetes internals (control plane, networking, storage, scheduling)
- Container runtime issues (containerd, CRI-O, Docker)
- Linux systems programming and debugging
- Distributed systems failure patterns
- Cloud provider Kubernetes (EKS, GKE, AKS)
- Service mesh (Istio, Linkerd, Cilium)
- Observability (Prometheus, Grafana, Jaeger, Loki)

Your task is to analyze Kubernetes troubleshooting evidence and provide a precise, actionable diagnosis.

You must respond with a structured JSON object containing exactly these fields:
1. root_cause: One-sentence root cause statement
2. explanation: Detailed technical explanation of the failure
3. fix: Specific, actionable fix with kubectl commands
4. kubectl_commands: Array of kubectl commands to execute
5. prevention: Long-term prevention recommendation
6. confidence: Integer 0-100 representing your confidence

Rules:
- Be specific and technical - avoid generic advice
- Correlate multiple evidence sources (pods, logs, events, deployments, network)
- If evidence is insufficient, state what's missing
- Confidence must reflect evidence quality
- Commands must be copy-paste ready
- No markdown formatting in JSON response"""


def build_investigation_prompt(investigation: dict[str, Any]) -> list[dict[str, str]]:
    """Build the prompt messages for LLM."""

    # Extract and summarize evidence
    pods_summary = _summarize_pods(investigation.get("pods", {}))
    logs_summary = _summarize_logs(investigation.get("logs", {}))
    events_summary = _summarize_events(investigation.get("events", {}))
    deployments_summary = _summarize_deployments(investigation.get("deployments", {}))
    network_summary = _summarize_network(investigation.get("network", {}))
    summary = investigation.get("summary", {})

    user_prompt = f"""Analyze this Kubernetes investigation evidence and provide a diagnosis.

## Investigation Summary
- Namespace: {investigation.get('namespace', 'all')}
- Overall Healthy: {summary.get('overall_healthy', 'unknown')}
- Total Issues: {summary.get('total_issues', 0)}
- Critical Issues: {len(summary.get('critical_issues', []))}

## Pod Status
{pods_summary}

## Logs Analysis
{logs_summary}

## Events Analysis
{events_summary}

## Deployment Health
{deployments_summary}

## Networking Findings
{network_summary}

Provide your diagnosis as JSON with: root_cause, explanation, fix, kubectl_commands, prevention, confidence."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _summarize_pods(pods: dict[str, Any]) -> str:
    """Summarize pod findings."""
    if not pods:
        return "No pod data available"

    if "error" in pods:
        return f"Error fetching pods: {pods['error']}"

    problematic = pods.get("problematic_pods", [])
    if not problematic:
        return f"All {pods.get('total_pods', 0)} pods healthy"

    lines = [f"Found {len(problematic)} problematic pod(s):"]
    for pod in problematic[:10]:  # Limit to top 10
        lines.append(f"  - {pod.get('namespace')}/{pod.get('name')}: {pod.get('status')} - {', '.join(pod.get('issues', [])[:3])}")

    return "\n".join(lines)


def _summarize_logs(logs: dict[str, Any]) -> str:
    """Summarize log findings."""
    if not logs:
        return "No log data available"

    lines = []
    for key, data in list(logs.items())[:10]:  # Limit to top 10
        if "error" in data:
            lines.append(f"  {key}: Error - {data['error']}")
        elif "analysis" in data:
            analysis = data["analysis"]
            findings = analysis.get("findings", [])
            if findings:
                lines.append(f"  {key}: {len(findings)} finding(s)")
                for f in findings[:3]:
                    lines.append(f"    - {f['type']}: {f['count']} occurrences")
            elif analysis.get("has_errors"):
                lines.append(f"  {key}: Errors detected in logs")
            else:
                lines.append(f"  {key}: No clear error patterns")

    return "\n".join(lines) if lines else "No log data collected"


def _summarize_events(events: dict[str, Any]) -> str:
    """Summarize event findings."""
    if not events:
        return "No event data available"

    if "error" in events:
        return f"Error fetching events: {events['error']}"

    critical = events.get("critical_events", [])
    warning = events.get("warning_events", [])
    summary = events.get("summary", {})

    lines = [f"Total events: {summary.get('total_events', 0)}"]
    lines.append(f"Critical: {summary.get('critical_count', 0)}, Warning: {summary.get('warning_count', 0)}")

    if critical:
        lines.append("Top critical events:")
        for e in critical[:5]:
            obj = e.get("object", {})
            lines.append(f"  - {obj.get('namespace')}/{obj.get('kind')}/{obj.get('name')}: {e.get('reason')} (x{e.get('count', 1)})")

    return "\n".join(lines)


def _summarize_deployments(deployments: dict[str, Any]) -> str:
    """Summarize deployment findings."""
    if not deployments:
        return "No deployment data available"

    if "error" in deployments:
        return f"Error fetching deployments: {deployments['error']}"

    problematic = deployments.get("problematic_deployments", [])
    if not problematic:
        return f"All {deployments.get('total_deployments', 0)} deployments healthy"

    lines = [f"Found {len(problematic)} problematic deployment(s):"]
    for dep in problematic[:10]:
        replicas = dep.get("replicas", {})
        lines.append(f"  - {dep.get('namespace')}/{dep.get('name')}: {dep.get('status')} - desired={replicas.get('desired')}, available={replicas.get('available')}, unavailable={replicas.get('unavailable')}")

    return "\n".join(lines)


def _summarize_network(network: dict[str, Any]) -> str:
    """Summarize network findings."""
    if not network:
        return "No network data available"

    if "error" in network:
        return f"Error fetching network: {network['error']}"

    problematic = network.get("problematic_services", [])
    without_endpoints = network.get("services_without_endpoints", [])

    lines = [f"Total services: {network.get('total_services', 0)}"]

    if problematic:
        lines.append(f"Problematic services: {len(problematic)}")
        for svc in problematic[:5]:
            lines.append(f"  - {svc.get('namespace')}/{svc.get('name')}: {', '.join(svc.get('issues', [])[:2])}")

    if without_endpoints:
        lines.append(f"Services without endpoints: {len(without_endpoints)}")
        for svc in without_endpoints[:5]:
            lines.append(f"  - {svc.get('namespace')}/{svc.get('name')}: selector={svc.get('selector')}")

    return "\n".join(lines) if lines else "All services healthy"
