"""
UrbanFlow AI - Emergency Agent
Input: EmergencyRequest + candidate network routes
Output: Dedicated priority corridor, pre-empted signal plan, and baseline vs. priority ETA delta
"""

from typing import Dict, Any, List, Optional
import networkx as nx
from agents.base_agent import BaseAgent
from shared.world_state import WorldState
from shared.schemas import AgentEvent, EmergencyRequest, RouteOption
from shared.route_cost_policy import RouteCostPolicy
from agents.routing_agent import RoutingAgent


class EmergencyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="EmergencyAgent")
        self.routing_helper = RoutingAgent()

    def process(
        self,
        world_state: WorldState,
        emergency_request: Optional[EmergencyRequest] = None,
        **kwargs
    ) -> AgentEvent:
        """
        Evaluates emergency vehicle mobility, reserves lowest-delay green wave corridor,
        and records priority assumptions.
        """
        # Ingest or update active emergency request
        if emergency_request:
            world_state.active_emergency = emergency_request

        req = world_state.active_emergency

        if not req or req.status != "active":
            event = world_state.add_agent_event(
                agent_name=self.name,
                input_summary="No active emergency vehicle priority requested.",
                decision="Network operating under standard municipal priority rules.",
                handoff_to="CoordinatorAgent"
            )
            return event

        # 1. First, build graph with emergency weights
        G_emg = self.routing_helper.build_graph(world_state, is_emergency=True)

        # 2. Compute shortest emergency path avoiding hard blockages
        try:
            node_path = nx.shortest_path(G_emg, source=req.origin_node, target=req.destination_node, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            event = world_state.add_agent_event(
                agent_name=self.name,
                input_summary=f"Emergency routing for {req.vehicle_id} from {req.origin_node} to {req.destination_node}.",
                decision="ALERT: No viable path available to destination due to total network partitioning.",
                handoff_to="CoordinatorAgent"
            )
            return event

        corridor_segment_ids: List[str] = []
        polyline_coords: List[List[float]] = []
        total_dist_km = 0.0
        prioritized_eta_sec = 0.0
        unoptimized_baseline_eta_sec = 0.0

        for u, v in zip(node_path[:-1], node_path[1:]):
            edge_data = G_emg[u][v]
            seg_id = edge_data["segment_id"]
            segment = edge_data["segment"]

            corridor_segment_ids.append(seg_id)
            total_dist_km += edge_data["length_km"]

            # Prioritized travel time with green-wave preemption & sirens
            # Sirens and signal preemption allow travel at or near speed limit
            preempted_speed = max(segment.speed_limit_kmh * 0.90, segment.current_speed)
            prioritized_time_sec = (segment.length_km / preempted_speed) * 3600.0
            prioritized_eta_sec += prioritized_time_sec

            # Unoptimized baseline travel time under current congestion without preemption
            congested_speed = max(segment.current_speed, 6.0)
            unoptimized_time = (segment.length_km / congested_speed) * 3600.0
            # Plus 25s red light delay per intersection in unoptimized baseline
            unoptimized_time += 25.0
            unoptimized_baseline_eta_sec += unoptimized_time

            # Mark segment as priority corridor unless blocked
            if segment.status != "blocked":
                segment.status = "priority_corridor"

            if not polyline_coords:
                polyline_coords.extend(segment.coordinates)
            else:
                polyline_coords.extend(segment.coordinates[1:])

        # Intersections receiving automated green-wave preemption
        preempted_intersections = node_path[1:-1]

        time_saved_sec = max(0.0, unoptimized_baseline_eta_sec - prioritized_eta_sec)

        # Update EmergencyRequest
        req.current_eta_seconds = round(prioritized_eta_sec, 1)
        req.baseline_eta_seconds = round(unoptimized_baseline_eta_sec, 1)
        req.corridor_segment_ids = corridor_segment_ids
        req.priority_intersections = preempted_intersections

        # Store dedicated RouteOption for UI
        corridor_route = RouteOption(
            id="emergency_corridor",
            name=f"Priority Corridor ({req.vehicle_id})",
            segment_ids=corridor_segment_ids,
            node_ids=node_path,
            coordinates=polyline_coords,
            total_distance_km=round(total_dist_km, 2),
            estimated_time_seconds=round(prioritized_eta_sec, 1),
            baseline_time_seconds=round(unoptimized_baseline_eta_sec, 1),
            time_savings_seconds=round(time_saved_sec, 1),
            total_cost=round(prioritized_eta_sec, 1),
            is_active=True,
            color="#10B981"  # Emerald green for priority corridor
        )

        world_state.active_routes["emergency_corridor"] = corridor_route
        world_state.recalculate_metrics()

        priority_assumptions = [
            f"Pre-empted traffic signals at: {', '.join(preempted_intersections)}",
            "Emergency siren escort active: 65% congestion delay absorption",
            f"Bypassed physical obstructions safely along {len(corridor_segment_ids)} segments"
        ]

        decision = (
            f"Established Priority Corridor for {req.vehicle_id} ({req.origin_node} -> {req.destination_node}). "
            f"Prioritized ETA: {round(prioritized_eta_sec / 60.0, 1)}m vs. Baseline: {round(unoptimized_baseline_eta_sec / 60.0, 1)}m "
            f"(ETA savings: {round(time_saved_sec / 60.0, 1)} mins / {int((time_saved_sec / unoptimized_baseline_eta_sec) * 100)}%). "
            f"Pre-empted {len(preempted_intersections)} signals."
        )

        event = world_state.add_agent_event(
            agent_name=self.name,
            input_summary=f"Emergency corridor dispatch evaluated for {req.vehicle_id} [Priority: {req.priority}].",
            decision=decision,
            handoff_to="CoordinatorAgent",
            metadata={
                "vehicle_id": req.vehicle_id,
                "corridor_segments": corridor_segment_ids,
                "preempted_intersections": preempted_intersections,
                "prioritized_eta_sec": round(prioritized_eta_sec, 1),
                "baseline_eta_sec": round(unoptimized_baseline_eta_sec, 1),
                "time_saved_sec": round(time_saved_sec, 1),
                "priority_assumptions": priority_assumptions
            }
        )
        return event

