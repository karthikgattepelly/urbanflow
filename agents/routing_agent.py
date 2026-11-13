"""
UrbanFlow AI - Routing Agent
Input: Road network graph + live dynamic edge costs
Output: Primary optimal route, alternative bypass routes, and baseline comparisons
"""

from typing import Dict, Any, List, Optional, Tuple
import networkx as nx
from agents.base_agent import BaseAgent
from shared.world_state import WorldState
from shared.schemas import AgentEvent, RouteOption, RoadSegment
from shared.route_cost_policy import RouteCostPolicy


class RoutingAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="RoutingAgent")

    def build_graph(
        self,
        world_state: WorldState,
        is_emergency: bool = False,
        corridor_segment_ids: Optional[List[str]] = None
    ) -> nx.DiGraph:
        """
        Constructs a directed NetworkX graph weighted by dynamic RouteCostPolicy.
        """
        G = nx.DiGraph()
        corridor_set = set(corridor_segment_ids or [])

        for seg_id, segment in world_state.segments.items():
            is_corridor = seg_id in corridor_set
            cost, breakdown = RouteCostPolicy.calculate_edge_cost(
                segment=segment,
                is_emergency=is_emergency,
                is_corridor=is_corridor
            )

            # Store edge with segment metadata
            G.add_edge(
                segment.start_node,
                segment.end_node,
                segment_id=seg_id,
                weight=cost,
                base_time=breakdown["base_travel_time_sec"],
                length_km=segment.length_km,
                segment=segment
            )
        return G

    def compute_route(
        self,
        G: nx.DiGraph,
        origin_node: str,
        destination_node: str,
        route_id: str,
        route_name: str,
        color: str,
        world_state: WorldState
    ) -> Optional[RouteOption]:
        """
        Calculates optimal shortest path via Dijkstra on dynamic edge weights.
        """
        try:
            node_path = nx.shortest_path(G, source=origin_node, target=destination_node, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        segment_ids: List[str] = []
        polyline_coords: List[List[float]] = []
        total_dist_km = 0.0
        total_cost = 0.0
        baseline_time_sec = 0.0
        estimated_time_sec = 0.0

        for u, v in zip(node_path[:-1], node_path[1:]):
            edge_data = G[u][v]
            seg_id = edge_data["segment_id"]
            segment = edge_data["segment"]

            segment_ids.append(seg_id)
            total_dist_km += edge_data["length_km"]
            total_cost += edge_data["weight"]

            # Travel time without non-traffic blocking penalties
            effective_speed = max(segment.current_speed, 5.0)
            travel_time_sec = (segment.length_km / effective_speed) * 3600.0
            estimated_time_sec += travel_time_sec

            base_time = (segment.length_km / max(segment.baseline_speed, 10.0)) * 3600.0
            baseline_time_sec += base_time

            # Accumulate coordinates
            if not polyline_coords:
                polyline_coords.extend(segment.coordinates)
            else:
                polyline_coords.extend(segment.coordinates[1:])

        return RouteOption(
            id=route_id,
            name=route_name,
            segment_ids=segment_ids,
            node_ids=node_path,
            coordinates=polyline_coords,
            total_distance_km=round(total_dist_km, 2),
            estimated_time_seconds=round(estimated_time_sec, 1),
            baseline_time_seconds=round(baseline_time_sec, 1),
            time_savings_seconds=0.0,
            total_cost=round(total_cost, 1),
            is_active=True,
            color=color
        )

    def process(
        self,
        world_state: WorldState,
        origin_node: str = "N_WEST_GATE",
        destination_node: str = "N_HOSPITAL_PLAZA",
        **kwargs
    ) -> AgentEvent:
        """
        Computes the primary dynamic route and an alternative route.
        """
        # If an emergency request exists, match origin and destination
        if world_state.active_emergency and world_state.active_emergency.status == "active":
            origin_node = world_state.active_emergency.origin_node
            destination_node = world_state.active_emergency.destination_node

        G_live = self.build_graph(world_state, is_emergency=False)

        # 1. Primary route
        primary_route = self.compute_route(
            G=G_live,
            origin_node=origin_node,
            destination_node=destination_node,
            route_id="primary",
            route_name="Dynamic Optimal Route",
            color="#3B82F6",
            world_state=world_state
        )

        # 2. Alternative route (penalize primary segments to force a diverse bypass)
        G_alt = G_live.copy()
        if primary_route:
            for seg_id in primary_route.segment_ids:
                # Find edge and amplify weight
                for u, v, data in G_alt.edges(data=True):
                    if data["segment_id"] == seg_id:
                        data["weight"] += 500.0

        alt_route = self.compute_route(
            G=G_alt,
            origin_node=origin_node,
            destination_node=destination_node,
            route_id="alternative",
            route_name="Secondary Bypass Route",
            color="#8B5CF6",
            world_state=world_state
        )

        routes_dict: Dict[str, RouteOption] = {}
        if primary_route:
            routes_dict["primary"] = primary_route
        if alt_route:
            routes_dict["alternative"] = alt_route

        world_state.active_routes = routes_dict

        # Evaluate if reroute occurred
        has_blocked_segment = any(
            world_state.segments[s].status == "blocked" for s in world_state.segments
        )
        avoided_str = ""
        if primary_route and has_blocked_segment:
            blocked_ids = [s for s in world_state.segments if world_state.segments[s].status == "blocked"]
            if not any(s in primary_route.segment_ids for s in blocked_ids):
                avoided_str = f" Route safely diverted around obstruction ({', '.join(blocked_ids)})."

        decision = (
            f"Optimized path from {origin_node} to {destination_node}. "
            f"Primary ETA: {round(primary_route.estimated_time_seconds / 60.0, 1)}m ({primary_route.total_distance_km} km)."
            + (f" Alt ETA: {round(alt_route.estimated_time_seconds / 60.0, 1)}m." if alt_route else "")
            + avoided_str
        )

        event = world_state.add_agent_event(
            agent_name=self.name,
            input_summary=f"Evaluated live edge costs from {origin_node} to {destination_node}.",
            decision=decision,
            handoff_to="EmergencyAgent",
            metadata={
                "origin": origin_node,
                "destination": destination_node,
                "primary_segments": primary_route.segment_ids if primary_route else [],
                "primary_cost": primary_route.total_cost if primary_route else 0.0,
                "primary_eta_sec": primary_route.estimated_time_seconds if primary_route else 0.0,
                "alt_segments": alt_route.segment_ids if alt_route else []
            }
        )
        return event

