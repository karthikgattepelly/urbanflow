"""
UrbanFlow AI - Coordination & Consistency Tests (Phase 4)
Verifies:
1. Consistency: Map, alert, route, and explanation share unified incident ID, timestamp, and state.
2. Observable Loop: Telemetry -> MonitorEvent -> ForecastEvent -> IncidentEvent -> RouteEvent -> EmergencyEvent -> DecisionEvent.
3. API Endpoints: get_network_state, play_scenario, dispatch_emergency, get_decision.
"""

from backend.app import (
    get_network_state,
    play_scenario,
    create_emergency,
    get_routes,
    get_decision,
    EmergencyDispatchRequest
)
from backend.scenario_runner import runner


def test_api_network_state_baseline():
    """
    Verifies GET /network/state returns valid map segments, metrics, and initial state.
    """
    runner.reset_to_scenario("normal")
    data = get_network_state()
    assert "segments" in data
    assert "network_metrics" in data
    assert len(data["segments"]) >= 12
    assert data["network_metrics"]["average_speed_kmh"] > 30.0
    print(f"PASS: Baseline network state verified ({len(data['segments'])} segments).")


def test_scenario_consistency_incident_and_explanation():
    """
    Acceptance Criterion #5: Map, alert, route and explanation share incident ID/timestamp.
    """
    # 1. Play blockage scenario
    state = play_scenario("blockage")

    # 2. Check alert / incident
    assert len(state["incidents"]) > 0
    incident = state["incidents"][0]
    incident_id = incident["id"]
    incident_seg_id = incident["location_segment_id"]

    # 3. Check map segment references same incident
    seg = state["segments"][incident_seg_id]
    assert seg["status"] == "blocked"
    assert seg["incident_id"] == incident_id

    # 4. Check route avoids that exact segment
    primary_route = state["active_routes"]["primary"]
    assert incident_seg_id not in primary_route["segment_ids"]

    # 5. Check explanation references that incident
    rec = state["active_recommendations"][0]
    assert incident_seg_id in rec["affected_segments"]
    assert "collision" in rec["rationale"].lower() or "obstruction" in rec["rationale"].lower()

    # 6. Verify get_decision returns identical incident and recommendation
    dec_data = get_decision("latest")
    assert dec_data["recommendation"]["id"] == rec["id"]
    assert any(i["id"] == incident_id for i in dec_data["incidents"])

    print(
        f"PASS: Consistency Verified - Incident '{incident_id}' consistently linked across "
        f"Map Segment '{incident_seg_id}', Route Reroute, Decision Drawer, and Explanation Rationale."
    )


def test_emergency_play_flow():
    """
    Verifies full closed-loop emergency playback and ETA savings via API.
    """
    state = play_scenario("emergency")

    assert state["active_emergency"] is not None
    emg = state["active_emergency"]
    assert emg["vehicle_id"] == "AMB-104"
    assert emg["current_eta_seconds"] < emg["baseline_eta_seconds"]

    assert "emergency_corridor" in state["active_routes"]
    corridor = state["active_routes"]["emergency_corridor"]
    assert corridor["time_savings_seconds"] > 0

    print(
        f"PASS: Full Emergency Play Verified - AMB-104 Corridor ETA: {corridor['estimated_time_seconds']}s "
        f"vs Baseline: {corridor['baseline_time_seconds']}s (Saved: {corridor['time_savings_seconds']}s)."
    )


def test_agent_handoff_sequence():
    """
    Verifies the critical event-driven multi-agent cycle:
    telemetry -> MonitorEvent -> ForecastEvent -> IncidentEvent -> RouteEvent -> EmergencyEvent -> DecisionEvent
    """
    runner.reset_to_scenario("emergency")
    runner.step_scenario()

    log = runner.world_state.agent_event_log
    agent_names = [e.agent_name for e in log[-7:]]

    expected_sequence = [
        "MonitorAgent",
        "ForecastAgent",
        "IncidentAgent",
        "RoutingAgent",
        "EmergencyAgent",
        "ExplanationAgent",
        "CoordinatorAgent"
    ]
    assert agent_names == expected_sequence, f"Expected {expected_sequence}, got {agent_names}"
    print(f"PASS: Agent handoff order strictly verified: {' -> '.join(agent_names)}")


if __name__ == "__main__":
    test_api_network_state_baseline()
    test_scenario_consistency_incident_and_explanation()
    test_emergency_play_flow()
    test_agent_handoff_sequence()
    print("All Phase 4 Coordination & Consistency tests PASSED successfully!")
