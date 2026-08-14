import re
from threading import Lock
from typing import Dict, Any, List

class MetricsRegistry:
    """
    Production-grade, high-performance Metrics Registry.
    Tracks HTTP, Worker, Pipeline Stage, AI Provider, and Database operational metrics
    without high-cardinality label pollution (omits candidate_id, email, resume_id).
    """

    def __init__(self):
        self._lock = Lock()
        
        # Counters
        self._counters: Dict[str, float] = {}
        
        # Histograms / Durations (stored as sum and count)
        self._durations: Dict[str, Dict[str, float]] = {}

    def _format_key(self, metric_name: str, labels: Dict[str, str]) -> str:
        if not labels:
            return metric_name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{metric_name}{{{label_str}}}"

    def increment(self, metric_name: str, value: float = 1.0, labels: Dict[str, str] = None):
        key = self._format_key(metric_name, labels or {})
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + value

    def observe_duration(self, metric_name: str, duration_sec: float, labels: Dict[str, str] = None):
        key = self._format_key(metric_name, labels or {})
        with self._lock:
            if key not in self._durations:
                self._durations[key] = {"count": 0.0, "sum": 0.0}
            self._durations[key]["count"] += 1.0
            self._durations[key]["sum"] += duration_sec

    def normalize_path(self, path: str) -> str:
        """Sanitizes HTTP request path to avoid high cardinality."""
        # Replace UUIDs with {id}
        path = re.sub(r'/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', '/{id}', path)
        return path

    def export_prometheus(self) -> str:
        """Returns Prometheus text format metrics string."""
        lines: List[str] = []
        with self._lock:
            for key, val in sorted(self._counters.items()):
                lines.append(f"{key} {val}")
            for key, data in sorted(self._durations.items()):
                lines.append(f"{key}_count {data['count']}")
                lines.append(f"{key}_sum {round(data['sum'], 4)}")
        return "\n".join(lines) + "\n"

    def export_json(self) -> Dict[str, Any]:
        """Returns JSON snapshot of all system metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "durations": dict(self._durations),
            }

metrics = MetricsRegistry()
