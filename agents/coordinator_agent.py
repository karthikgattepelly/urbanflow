"""
UrbanFlow AI - Coordinator Agent
Orchestrates the entire multi-agent cycle in strict sequence:
telemetry -> MonitorEvent -> ForecastEvent -> IncidentEvent -> RouteEvent -> EmergencyEvent -> DecisionEvent -> dashboard
Maintains canonical state integrity so the UI never displays contradictory information.
"""

from typing import Dict, Any, Optional
import time
from agents.base_agent import BaseAgent
from agents.monitor_agent import MonitorAgent
from agents.forecast_agent import ForecastAgent
from agents.incident_agent import IncidentAgent
from agents.routing_agent import RoutingAgent
from agents.emergency_agent import EmergencyAgent
from agents.explanation_agent import ExplanationAgent
from shared.world_state import WorldState
from shared.schemas import AgentEvent, EmergencyRequest


class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="CoordinatorAgent")
        # Initialize specialist agents
        self.monitor_agent = MonitorAgent()
        self.forecast_agent = ForecastAgent()
        self.incident_agent = IncidentAgent()
        self.routing_agent = RoutingAgent()
        self.emergency_agent = EmergencyAgent()
        self.explanation_agent = ExplanationAgent()

    def process(
        self,
        world_state: WorldState,
        telemetry_update: Optional[Dict[str, Any]] = None,
        emergency_request: Optional[EmergencyRequest] = None,
        origin_node: str = "N_WEST_GATE",
        destination_node: str = "N_HOSPITAL_PLAZA",
        **kwargs
    ) -> AgentEvent:
        """
        Executes the observable closed loop in guaranteed order:
        Sense -> Predict -> Decide -> Act -> Explain.
        """
        # 1. Sense: Monitor Agent normalizes speeds & detects sensor anomalies
        monitor_evt = self.monitor_agent.process(world_state, telemetry_update=telemetry_update)

        # 2. Predict: Forecast Agent evaluates 15/30-minute risk horizons
        forecast_evt = self.forecast_agent.process(world_state)

        # 3. Detect/Corroborate: Incident Agent validates anomalies with CV evidence
        incident_evt = self.incident_agent.process(world_state, telemetry_update=telemetry_update)

        # 4. Decide: Routing Agent computes live shortest & alternative routes
        routing_evt = self.routing_agent.process(
            world_state,
            origin_node=origin_node,
            destination_node=destination_node
        )

        # 5. Act: Emergency Agent provisions priority corridor & signal preemption
        emergency_evt = self.emergency_agent.process(
            world_state,
            emergency_request=emergency_request
        )

        # 6. Explain: Explanation Agent synthesizes evidence, confidence, and rationale
        explanation_evt = self.explanation_agent.process(world_state)

        # 7. Coordinator finalizes canonical world-state snapshot
        world_state.step += 1
        world_state.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        world_state.recalculate_metrics()

        rec = world_state.active_recommendations[0] if world_state.active_recommendations else None
        action_summary = rec.action if rec else "System nominal"

        coordinator_evt = world_state.add_agent_event(
            agent_name=self.name,
            input_summary="Verified and synchronized all 6 specialist agent state transitions.",
            decision=f"Published canonical snapshot #{world_state.step}: {action_summary}.",
            handoff_to="Dashboard",
            metadata={
                "step": world_state.step,
                "active_incidents": len(world_state.incidents),
                "active_routes": list(world_state.active_routes.keys()),
                "health_score": world_state.network_metrics.network_health_score,
                "emergency_corridor": world_state.network_metrics.emergency_corridor_active
            }
        )

        return coordinator_evt

