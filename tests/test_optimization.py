"""
UrbanFlow AI - Optimization Tests (Phase 3)
Verifies:
1. Route: Closure avoids blocked edge and documents ETA delta.
2. Emergency: Priority route includes corridor and baseline comparison.
"""

import json
from pathlib import Path
from shared.schemas import RoadSegment, EmergencyRequest
from shared.world_state import WorldState
from agents.routing_agent import RoutingAgent
from agents.emergency_agent import EmergencyAgent


def load_test_world_state() -> WorldState:
    graph_path = Path(__file__).parent.parent / "data" / "district_graph.json"
    with open(graph_path, "r") as f:
        graph_data = json.load(f)

    world = WorldState()
    for seg_dict in graph_data["segments"]:
        segment = RoadSegment(
            id=seg_dict["id"],
            name=seg_dict["name"],
            start_node=seg_dict["start_node"],
            end_node=seg_dict["end_node"],
            length_km=seg_dict["length_km"],
            speed_limit_kmh=seg_dict["speed_limit_kmh"],
            current_speed=seg_dict["baseline_speed"],
            baseline_speed=seg_dict["baseline_speed"],
            occupancy=seg_dict["baseline_occupancy"],
            baseline_occupancy=seg_dict["baseline_occupancy"],
            coordinates=seg_dict["coordinates"]
        )
        world.segments[segment.id] = segment
    world.recalculate_metrics()
    return world


def test_dynamic_reroute_around_blockage():
    """
    Assertion: Closed/high-cost edge changes optimal path and avoids blocked edge.
    """
    world = load_test_world_state()
    routing_agent = RoutingAgent()

    origin = "N_WEST_GATE"
    destination = "N_HOSPITAL_PLAZA"

    # 1. Normal state route calculation
    routing_agent.process(world, origin_node=origin, destination_node=destination)
    initial_route = world.active_routes.get("primary")
    assert initial_route is not None
    # Under free flow, seg_03 is part of the shortest path
    assert "seg_03" in initial_route.segment_ids, "Expected seg_03 in nominal primary path"
    initial_eta = initial_route.estimated_time_seconds

    # 2. Block seg_03 (simulating heavy incident)
    world.segments["seg_03"].status = "blocked"
    world.segments["seg_03"].current_speed = 4.0

    # 3. Recalculate route
    routing_agent.process(world, origin_node=origin, destination_node=destination)
    rerouted_route = world.active_routes.get("primary")
    assert rerouted_route is not None

    # Assert seg_03 is strictly avoided
    assert "seg_03" not in rerouted_route.segment_ids, "Reroute must NOT traverse blocked seg_03"
    # Assert bypass segments are used (e.g. seg_04, seg_15, seg_07)
    assert any(s in rerouted_route.segment_ids for s in ["seg_04", "seg_15", "seg_07", "seg_14"])
    print(f"PASS: Dynamic Rerouting Verified - Path safely bypassed seg_03. New segments: {rerouted_route.segment_ids}")


def test_emergency_priority_corridor():
    """
    Assertion: Priority route beats baseline ETA and marks corridor.
    """
    world = load_test_world_state()
    emergency_agent = EmergencyAgent()

    # Block seg_03
    world.segments["seg_03"].status = "blocked"
    world.segments["seg_03"].current_speed = 5.0

    req = EmergencyRequest(
        id="emg_104",
        vehicle_id="AMB-104",
        vehicle_type="ambulance",
        origin_node="N_WEST_GATE",
        destination_node="N_HOSPITAL_PLAZA",
        eta_target_seconds=360.0,
        current_eta_seconds=0.0,
        baseline_eta_seconds=0.0,
        priority="critical",
        status="active"
    )

    emergency_agent.process(world, emergency_request=req)

    # 1. Check priority corridor route exists
    corridor_route = world.active_routes.get("emergency_corridor")
    assert corridor_route is not None, "Expected emergency_corridor in active_routes"

    # 2. Assert prioritized ETA beats baseline ETA
    assert corridor_route.estimated_time_seconds < corridor_route.baseline_time_seconds
    assert corridor_route.time_savings_seconds > 0.0

    # 3. Assert corridor segments marked as priority_corridor
    for seg_id in corridor_route.segment_ids:
        if seg_id != "seg_03":
            assert world.segments[seg_id].status == "priority_corridor"

    # 4. Assert priority intersections populated
    assert len(req.priority_intersections) > 0

    print(
        f"PASS: Emergency Corridor Verified - Prioritized ETA: {corridor_route.estimated_time_seconds}s "
        f"vs Baseline: {corridor_route.baseline_time_seconds}s (Saved: {corridor_route.time_savings_seconds}s). "
        f"Preempted Intersections: {req.priority_intersections}"
    )


if __name__ == "__main__":
    test_dynamic_reroute_around_blockage()
    test_emergency_priority_corridor()
    print("All Phase 3 Optimization tests PASSED successfully!")

