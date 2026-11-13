"""
UrbanFlow AI - Anomaly Scoring Model
Evaluates real-time sensor streams for sudden speed collapses,
occupancy spikes, and abnormal physical deviations.
"""

from typing import Dict, Any, Tuple


class AnomalyScorer:
    """
    Detects sensor-level telemetry anomalies such as rapid deceleration,
    phantom jams, or sudden physical lane obstructions.
    """

    SPEED_COLLAPSE_RATIO = 0.40  # Speed drops below 40% of baseline nominal
    OCCUPANCY_JAM_THRESHOLD = 0.85
    EXTREME_DECELERATION_KMH = 25.0

    @classmethod
    def score_telemetry(
        cls,
        current_speed: float,
        baseline_speed: float,
        current_occupancy: float,
        previous_speed: float = None
    ) -> Tuple[bool, float, str]:
        """
        Calculates (is_anomaly, anomaly_score, reason).
        Score is normalized in [0.0, 1.0].
        """
        safe_base = max(baseline_speed, 35.0)
        speed_ratio = current_speed / safe_base

        # Check sudden plunge
        is_sudden_plunge = False
        if previous_speed is not None and (previous_speed - current_speed) >= cls.EXTREME_DECELERATION_KMH:
            is_sudden_plunge = True

        reasons = []
        severity_score = 0.0

        if speed_ratio <= cls.SPEED_COLLAPSE_RATIO:
            reasons.append(f"speed_collapse_to_{round(current_speed, 1)}kmh")
            severity_score += 0.55

        if current_occupancy >= cls.OCCUPANCY_JAM_THRESHOLD:
            reasons.append(f"occupancy_spike_{round(current_occupancy * 100, 1)}pct")
            severity_score += 0.35

        if is_sudden_plunge:
            reasons.append("extreme_instant_deceleration")
            severity_score += 0.25

        anomaly_score = round(min(1.0, severity_score), 3)
        is_anomaly = anomaly_score >= 0.50

        reason_str = " | ".join(reasons) if reasons else "nominal_flow"
        return is_anomaly, anomaly_score, reason_str

