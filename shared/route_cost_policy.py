"""
UrbanFlow AI - Route Cost Policy
Implements the exact cost function defined in Build Instructions Section 5:
edge_cost = base_travel_time * congestion_multiplier + incident_penalty + reliability_penalty
Emergency routing favors reliable low-delay corridors and records every priority assumption.
"""

from typing import Dict, Any, Tuple
from shared.schemas import RoadSegment


class RouteCostPolicy:
    # Tunable policy weights
    MIN_SPEED_KMH = 4.0
    HIGH_INCIDENT_PENALTY_SEC = 900.0      # 15 minutes penalty for major obstruction
    BLOCKAGE_PENALTY_SEC = 9999.0          # Virtually impassable
    CRITICAL_SEVERITY_MULTIPLIER = 1.5
    RELIABILITY_RISK_SCALE_SEC = 180.0     # Up to 3 minutes penalty for unhedged 15m risk
    EMERGENCY_PREEMPTION_DISCOUNT = 0.65   # Sirens & green waves absorb 65% of congestion delay

    @classmethod
    def calculate_edge_cost(
        cls,
        segment: RoadSegment,
        is_emergency: bool = False,
        is_corridor: bool = False
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculates edge cost and returns (total_cost, breakdown_dict).
        All cost units are normalized in equivalent travel seconds.
        """
        # 1. Base travel time (seconds)
        safe_base_speed = max(segment.baseline_speed, 10.0)
        base_travel_time = (segment.length_km / safe_base_speed) * 3600.0

        # 2. Congestion multiplier
        effective_speed = max(segment.current_speed, cls.MIN_SPEED_KMH)
        speed_factor = safe_base_speed / effective_speed

        # Incorporate occupancy pressure
        occ = max(0.0, min(1.0, segment.occupancy))
        occupancy_factor = 1.0 + (3.2 * (occ ** 2.2))
        raw_congestion_mult = max(speed_factor, occupancy_factor)

        if is_emergency and is_corridor:
            # Emergency signal preemption and siren escort significantly compress congestion delay
            congestion_multiplier = 1.0 + ((raw_congestion_mult - 1.0) * (1.0 - cls.EMERGENCY_PREEMPTION_DISCOUNT))
        else:
            congestion_multiplier = raw_congestion_mult

        # 3. Incident penalty
        incident_penalty = 0.0
        if segment.status == "blocked":
            incident_penalty = cls.BLOCKAGE_PENALTY_SEC
        elif segment.incident_id:
            incident_penalty = cls.HIGH_INCIDENT_PENALTY_SEC

        # 4. Reliability penalty (forecast-ahead hedging)
        # Segments forecast to deteriorate within 15 minutes receive a reliability penalty
        reliability_penalty = segment.forecast_15m_risk * cls.RELIABILITY_RISK_SCALE_SEC

        # Special emergency corridor priority assumption:
        if is_emergency and is_corridor:
            # Corridor reservation guarantees prioritized transit
            reliability_penalty = 0.0

        total_cost = (base_travel_time * congestion_multiplier) + incident_penalty + reliability_penalty

        breakdown = {
            "base_travel_time_sec": round(base_travel_time, 2),
            "congestion_multiplier": round(congestion_multiplier, 3),
            "congestion_delay_sec": round(base_travel_time * (congestion_multiplier - 1.0), 2),
            "incident_penalty_sec": round(incident_penalty, 2),
            "reliability_penalty_sec": round(reliability_penalty, 2),
            "total_edge_cost_sec": round(total_cost, 2),
            "is_emergency_discounted": is_emergency and is_corridor
        }

        return round(total_cost, 2), breakdown

