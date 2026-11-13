"""
UrbanFlow AI - Monitor Agent
Input: Raw telemetry streams per road segment
Output: Normalized road state + detected sensor anomalies
"""

from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from shared.world_state import WorldState
from shared.schemas import AgentEvent
from models.anomaly_scoring import AnomalyScorer


class MonitorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MonitorAgent")

    def process(
        self,
        world_state: WorldState,
        telemetry_update: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentEvent:
        """
        Normalizes segment speeds/occupancies and scans for physical sensor anomalies.
        """
        detected_anomalies: List[Dict[str, Any]] = []

        if telemetry_update:
            for seg_id, reading in telemetry_update.items():
                if seg_id in world_state.segments:
                    segment = world_state.segments[seg_id]
                    prev_speed = segment.current_speed

                    # Update raw state
                    new_speed = float(reading.get("speed", segment.current_speed))
                    new_occ = float(reading.get("occupancy", segment.occupancy))

                    segment.current_speed = new_speed
                    segment.occupancy = new_occ

                    # Score sensor telemetry for abrupt collapses or spikes
                    is_anomaly, score, reason = AnomalyScorer.score_telemetry(
                        current_speed=new_speed,
                        baseline_speed=segment.baseline_speed,
                        current_occupancy=new_occ,
                        previous_speed=prev_speed
                    )

                    # Explicit fixture flags can also affirm anomalies
                    if reading.get("sensor_anomaly"):
                        is_anomaly = True
                        score = max(score, 0.88)
                        reason = f"abrupt_sensor_collapse_reported | {reason}"

                    if is_anomaly:
                        detected_anomalies.append({
                            "segment_id": seg_id,
                            "segment_name": segment.name,
                            "score": score,
                            "reason": reason,
                            "speed": new_speed,
                            "occupancy": new_occ
                        })

        world_state.recalculate_metrics()

        # Decision summary
        if detected_anomalies:
            decision = (
                f"Flagged {len(detected_anomalies)} sensor anomaly candidate(s): "
                + ", ".join(f"{a['segment_id']} ({a['reason']})" for a in detected_anomalies)
            )
        else:
            decision = f"All {len(world_state.segments)} corridors streaming within nominal operational envelopes."

        event = world_state.add_agent_event(
            agent_name=self.name,
            input_summary=f"Processed telemetry update for {len(telemetry_update or {})} road segments.",
            decision=decision,
            handoff_to="ForecastAgent",
            metadata={
                "anomaly_count": len(detected_anomalies),
                "anomalies": detected_anomalies
            }
        )
        return event

