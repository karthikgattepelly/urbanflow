"""
UrbanFlow AI - Forecast Agent
Input: Segment state history & occupancy velocity
Output: 15/30-minute predictive congestion risks and risk tiers
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from shared.world_state import WorldState
from shared.schemas import AgentEvent
from models.forecast_baseline import ForecastBaselineModel


class ForecastAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ForecastAgent")
        # Stores prior occupancies for velocity tracking {seg_id: prev_occ}
        self.occupancy_history: Dict[str, float] = {}

    def process(self, world_state: WorldState, **kwargs) -> AgentEvent:
        """
        Runs predictive forecast for each road segment.
        Identifies impending corridor deterioration 15-30 minutes ahead.
        """
        high_risk_segments: List[Dict[str, Any]] = []

        for seg_id, segment in world_state.segments.items():
            prev_occ = self.occupancy_history.get(seg_id, segment.baseline_occupancy)

            # Predict future risks
            risk_15m, risk_30m, risk_level = ForecastBaselineModel.predict_risk(
                current_speed=segment.current_speed,
                baseline_speed=segment.baseline_speed,
                current_occupancy=segment.occupancy,
                previous_occupancy=prev_occ,
                time_delta_minutes=2.0
            )

            # Update segment state
            segment.forecast_15m_risk = risk_15m
            segment.forecast_30m_risk = risk_30m
            segment.risk_level = risk_level

            # Update history cache
            self.occupancy_history[seg_id] = segment.occupancy

            if risk_level in ["high", "critical"]:
                high_risk_segments.append({
                    "segment_id": seg_id,
                    "segment_name": segment.name,
                    "risk_15m": risk_15m,
                    "risk_30m": risk_30m,
                    "risk_level": risk_level,
                    "occupancy": segment.occupancy,
                    "current_speed": segment.current_speed
                })

        world_state.recalculate_metrics()

        if high_risk_segments:
            decision = (
                f"Elevated 15m congestion risk on {len(high_risk_segments)} corridor(s): "
                + ", ".join(f"{s['segment_id']} ({int(s['risk_15m'] * 100)}% risk)" for s in high_risk_segments)
                + ". Pre-emptive load shedding recommended."
            )
        else:
            decision = "Forecast indicates all network corridors will remain free-flowing over the next 30 minutes."

        event = world_state.add_agent_event(
            agent_name=self.name,
            input_summary=f"Computed 15m & 30m risk projections across {len(world_state.segments)} segments.",
            decision=decision,
            handoff_to="IncidentAgent",
            metadata={
                "high_risk_count": len(high_risk_segments),
                "high_risk_segments": high_risk_segments
            }
        )
        return event

