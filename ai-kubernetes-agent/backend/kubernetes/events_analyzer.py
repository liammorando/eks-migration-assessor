"""Events Analyzer - read and analyze Kubernetes events."""

from collections import defaultdict
from typing import Any

from core.logging import logger
from kubernetes.executor import KubectlExecutor, get_executor

EVENT_TYPES = {
    "Warning": ["FailedScheduling", "BackOff", "FailedMount", "FailedPull", "ErrImagePull",
                "Unhealthy", "Failed", "Killing", "InspectFailed", "FailedValidation",
                "FailedBinding", "VolumeMismatch", "DiskPressure", "MemoryPressure",
                "PIDPressure", "NetworkUnavailable", "NodeNotReady", "NodeUnreachable"],
    "Normal": ["Scheduled", "Pulling", "Pulled", "Created", "Started", "SuccessfulCreate",
               "SuccessfulDelete", "ScalingReplicaSet", "REPLICASET", "DEPLOYMENT"],
}


class EventsAnalyzer:
    """Analyze Kubernetes events for issues."""

    def __init__(self, executor: KubectlExecutor | None = None):
        self.executor = executor or get_executor()

    def analyze(self, namespace: str | None = None) -> dict[str, Any]:
        """Analyze events across all or specific namespace."""
        logger.info("Analyzing Kubernetes events...")
        events_data = self.executor.get_events(all_namespaces=namespace is None, namespace=namespace)

        if "error" in events_data:
            logger.error(f"Failed to get events: {events_data.get('error')}")
            return {
                "error": events_data.get("error"),
                "critical_events": [],
                "warning_events": [],
                "summary": {},
            }

        return self._process_events(events_data.get("items", []))

    def _process_events(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Process and categorize events."""
        critical_events = []
        warning_events = []
        normal_events = []
        event_counts = defaultdict(int)
        involved_objects = defaultdict(list)

        for event in events:
            event_type = event.get("type", "Normal")
            reason = event.get("reason", "")
            message = event.get("message", "")
            count = event.get("count", 1)
            involved_object = event.get("involvedObject", {})
            obj_name = involved_object.get("name", "unknown")
            obj_kind = involved_object.get("kind", "unknown")
            obj_namespace = involved_object.get("namespace", "default")

            event_summary = {
                "type": event_type,
                "reason": reason,
                "message": message,
                "count": count,
                "object": {
                    "kind": obj_kind,
                    "name": obj_name,
                    "namespace": obj_namespace,
                },
                "first_timestamp": event.get("firstTimestamp"),
                "last_timestamp": event.get("lastTimestamp"),
            }

            # Categorize
            is_critical = False
            is_warning = False

            if event_type == "Warning":
                if reason in EVENT_TYPES["Warning"]:
                    is_critical = True
                else:
                    is_warning = True
            elif event_type == "Normal" and reason in EVENT_TYPES["Warning"]:
                is_warning = True

            if is_critical:
                critical_events.append(event_summary)
            elif is_warning:
                warning_events.append(event_summary)
            else:
                normal_events.append(event_summary)

            # Track counts
            key = f"{obj_namespace}/{obj_kind}/{obj_name}/{reason}"
            event_counts[key] += count
            involved_objects[key].append(event_summary)

        # Sort by count descending
        critical_events.sort(key=lambda x: x["count"], reverse=True)
        warning_events.sort(key=lambda x: x["count"], reverse=True)

        # Build summary
        summary = {
            "total_events": len(events),
            "critical_count": len(critical_events),
            "warning_count": len(warning_events),
            "normal_count": len(normal_events),
            "top_issues": self._get_top_issues(event_counts),
        }

        return {
            "critical_events": critical_events[:50],  # Limit to top 50
            "warning_events": warning_events[:50],
            "summary": summary,
        }

    def _get_top_issues(self, event_counts: dict[str, int]) -> list[dict[str, Any]]:
        """Get top issues by frequency."""
        sorted_issues = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"issue": issue, "count": count}
            for issue, count in sorted_issues[:10]
        ]


def analyze_events(namespace: str | None = None, executor: KubectlExecutor | None = None) -> dict[str, Any]:
    """Convenience function to analyze events."""
    analyzer = EventsAnalyzer(executor)
    return analyzer.analyze(namespace)
