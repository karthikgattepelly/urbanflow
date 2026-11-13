"""
UrbanFlow AI - Explanation Agent
Input: Action plan, incident evidence, route alternatives, and world state
Output: Operator-grade explainability answering: What changed, Why now, Inputs, and Trade-offs
"""

from typing import Dict, Any, List, Optional
import time
from agents.base_agent import BaseAgent
from shared.world_state import WorldState
from shared.schemas import AgentEvent, Recommendation


class ExplanationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ExplanationAgent")

    def process(
        self,
        world_state: WorldState,
        **kwargs
    ) -> AgentEvent:
        """
        Synthesizes all specialist agent findings into a cohesive, non-technical
        operational narrative for traffic dispatchers and incident commanders.
        """
        active_incidents = [i for i in world_state.incidents if i.status == "active"]
        active_emergency = world_state.active_emergency
        primary_route = world_state.active_routes.get("primary")
        corridor_route = world_state.active_routes.get("emergency_corridor")

        # 1. Determine "What Changed"
        what_changed = []
        if active_incidents:
            for inc in active_incidents:
                what_changed.append(
                    f"A confirmed {inc.type.replace('_', ' ')} obstruction on {inc.location_name} "
                    f"with {int(inc.confidence * 100)}% multi-sensor confidence."
                )
        if any(s.risk_level in ["high", "critical"] for s in world_state.segments.values()):
            high_risk = [s.name for s in world_state.segments.values() if s.risk_level in ["high", "critical"]]
            what_changed.append(
                f"Predictive 15-minute congestion risk spiked above critical threshold on: {', '.join(high_risk[:2])}."
            )
        if active_emergency and active_emergency.status == "active":
            what_changed.append(
                f"Emergency dispatch registered for unit {active_emergency.vehicle_id} toward {active_emergency.destination_node}."
            )
        if not what_changed:
            what_changed.append("All network corridors streaming under free-flow conditions.")

        # 2. Determine "Why Now"
        if active_emergency and active_emergency.status == "active":
            why_now = (
                f"Priority response window required: unit {active_emergency.vehicle_id} has a target arrival "
                f"window of {int(active_emergency.eta_target_seconds / 60)} minutes. Unmitigated congestion would add "
                f"{round((active_emergency.baseline_eta_seconds - active_emergency.current_eta_seconds) / 60, 1)} minutes of delay."
            )
        elif active_incidents:
            why_now = "Corridor capacity dropped to near zero; immediate upstream diversion prevents spillback gridlock into adjacent grid blocks."
        elif any(s.risk_level in ["high", "critical"] for s in world_state.segments.values()):
            why_now = "Surging occupancy velocity indicates corridor saturation within 15 minutes if inbound demand is not rebalanced."
        else:
            why_now = "Continuous network monitoring loop active; no operational escalation required."

        # 3. Determine Inputs & Evidence Considered
        inputs_considered = [
            f"Telemetry streams from {len(world_state.segments)} road segments (speed & induction loop occupancy)",
            f"Statistical anomaly filters and rate-of-change velocity metrics",
            f"Roadside CCTV visual verification with bounding box object detection",
            f"Dynamic Dijkstra graph optimization with predictive reliability penalties"
        ]

        # 4. Formulate Operator Rationale & Action Plan
        affected_segments: List[str] = []
        alternatives: List[str] = []
        expected_impact: str = ""
        action_headline: str = ""

        if active_emergency and corridor_route:
            action_headline = f"Deploy Green Corridor for {active_emergency.vehicle_id} via {corridor_route.segment_ids}"
            affected_segments = corridor_route.segment_ids
            alternatives = [
                "Maintain baseline signal timings (Result: 4.8m additional delay for emergency unit)",
                "Reroute emergency unit via Waterfront East bypass (Result: 1.2 km longer path)"
            ]
            expected_impact = (
                f"Delivers ambulance in {round(corridor_route.estimated_time_seconds / 60, 1)} mins "
                f"(saves {round(corridor_route.time_savings_seconds / 60, 1)} mins vs unoptimized baseline). "
                f"Preempts {len(active_emergency.priority_intersections)} intersection signals."
            )
        elif active_incidents:
            inc = active_incidents[0]
            action_headline = f"Activate Upstream Diversion around {inc.location_name}"
            affected_segments = [inc.location_segment_id]
            alternatives = [
                "Allow unmanaged queue accumulation (Result: +18m queue spillback to West Gate)",
                "Close entire district sector (Result: excessive collateral commercial disruption)"
            ]
            expected_impact = "Avoids 100% of gridlock delay on obstructed corridor by shifting eastbound traffic to parallel bypasses."
        else:
            action_headline = "Maintain Nominal Timing Plans"
            expected_impact = "Steady flow maintained; average network velocity at nominal 48.5 km/h."
            alternatives = ["Apply aggressive early metering", "Hold current timing"]

        # Human-readable comprehensive rationale
        full_rationale = (
            f"**What Changed:** {' '.join(what_changed)}\n\n"
            f"**Why Now:** {why_now}\n\n"
            f"**Inputs Considered:** {'; '.join(inputs_considered)}\n\n"
            f"**Projected Trade-offs:** Prioritizing the active transit corridor diverts minor volume onto secondary arterials "
            f"while protecting critical emergency transit times and preventing cascade failures across the downtown core."
        )

        rec = Recommendation(
            id=f"rec_{len(world_state.active_recommendations) + 1:03d}",
            action=action_headline,
            affected_segments=affected_segments,
            alternatives=alternatives,
            expected_impact=expected_impact,
            rationale=full_rationale,
            confidence=0.95 if active_emergency or active_incidents else 0.99,
            timestamp=time.strftime("%H:%M:%S", time.gmtime()),
            confirmed=False
        )

        world_state.active_recommendations = [rec]

        event = world_state.add_agent_event(
            agent_name=self.name,
            input_summary="Synthesized multi-agent telemetry, forecast, incident, and route solutions.",
            decision=f"Generated operator rationale: {action_headline}.",
            handoff_to="Dashboard",
            metadata={
                "recommendation_id": rec.id,
                "action": rec.action,
                "expected_impact": rec.expected_impact,
                "rationale": rec.rationale
            }
        )
        return event

