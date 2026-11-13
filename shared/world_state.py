"""
UrbanFlow AI - Canonical Shared World State
Maintains the single source of truth for the entire command center.
Agents publish events to this world model; the Coordinator Agent publishes snapshots.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import time
from shared.schemas import (
    RoadSegment,
    Incident,
    EmergencyRequest,
    RouteOption,
    Recommendation,
    AgentEvent
)


class NetworkMetrics(BaseModel):
    average_speed_kmh: float = Field(default=48.5)
    average_occupancy: float = Field(default=0.28)
    network_health_score: float = Field(default=95.0, description="Health percentage 0-100")
    active_alerts_count: int = Field(default=0)
    emergency_corridor_active: bool = Field(default=False)
    total_active_incidents: int = Field(default=0)


class WorldState(BaseModel):
    """
    Canonical world model snapshot. Only Coordinator Agent publishes modifications.
    """
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    scenario_id: str = Field(default="normal")
    step: int = Field(default=0)
    segments: Dict[str, RoadSegment] = Field(default_factory=dict)
    incidents: List[Incident] = Field(default_factory=list)
    active_emergency: Optional[EmergencyRequest] = Field(default=None)
    active_routes: Dict[str, RouteOption] = Field(default_factory=dict)
    active_recommendations: List[Recommendation] = Field(default_factory=list)
    agent_event_log: List[AgentEvent] = Field(default_factory=list)
    network_metrics: NetworkMetrics = Field(default_factory=NetworkMetrics)

    def add_agent_event(
        self,
        agent_name: str,
        input_summary: str,
        decision: str,
        handoff_to: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentEvent:
        event = AgentEvent(
            event_id=f"evt_{len(self.agent_event_log) + 1:04d}",
            agent_name=agent_name,
            timestamp=time.strftime("%H:%M:%S", time.gmtime()),
            input_summary=input_summary,
            decision=decision,
            handoff_to=handoff_to,
            metadata=metadata or {}
        )
        self.agent_event_log.append(event)
        return event

    def recalculate_metrics(self) -> None:
        if not self.segments:
            return
        total_speed = sum(s.current_speed for s in self.segments.values())
        total_occ = sum(s.occupancy for s in self.segments.values())
        n = len(self.segments)
        avg_speed = total_speed / n
        avg_occ = total_occ / n

        # Health score: 100 when speed is nominal and occupancy is low
        speed_ratio = min(1.0, avg_speed / 50.0)
        occ_penalty = max(0.0, avg_occ - 0.3) * 50.0
        health = max(10.0, min(100.0, (speed_ratio * 100.0) - occ_penalty - (len(self.incidents) * 15.0)))

        self.network_metrics.average_speed_kmh = round(avg_speed, 1)
        self.network_metrics.average_occupancy = round(avg_occ, 3)
        self.network_metrics.network_health_score = round(health, 1)
        self.network_metrics.active_alerts_count = len(self.incidents) + sum(
            1 for s in self.segments.values() if s.risk_level in ["high", "critical"]
        )
        self.network_metrics.total_active_incidents = len([i for i in self.incidents if i.status == "active"])
        self.network_metrics.emergency_corridor_active = bool(
            self.active_emergency and self.active_emergency.status == "active"
        )
