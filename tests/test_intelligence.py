"""
UrbanFlow AI - Intelligence Tests (Phase 2)
Verifies:
1. Forecast: Rising occupancy increases target-segment 15-minute risk before speed collapse.
2. Incident: CV/sensor anomaly creates candidate and raises nearby edge costs.
"""

import json
from pathlib import Path
from shared.schemas import RoadSegment
from shared.world_state import WorldState
from shared.route_cost_policy import RouteCostPolicy
from models.forecast_baseline import ForecastBaselineModel
from models.anomaly_scoring import AnomalyScorer
from agents.monitor_agent import MonitorAgent
from agents.forecast_agent import ForecastAgent
from agents.incident_agent import IncidentAgent


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


def test_forecast_early_warning():
    """
    Assertion: Rising occupancy increases target-segment 15-minute risk BEFORE speed collapses.
    """
    world = load_test_world_state()
    monitor = MonitorAgent()
    forecast = ForecastAgent()

    target_seg = "seg_03"
    initial_segment = world.segments[target_seg]
    base_speed = initial_segment.baseline_speed

    # Step 0: Initial baseline
    forecast.process(world)
    initial_risk = initial_segment.forecast_15m_risk
    assert initial_risk < 0.35, f"Expected low initial risk, got {initial_risk}"

    # Step 1: Inflow surges: occupancy rises from 0.28 to 0.65, but speed only drops moderately (50 -> 40 km/h)
    surge_telemetry = {
        target_seg: {"speed": 40.0, "occupancy": 0.65}
    }
    monitor.process(world, telemetry_update=surge_telemetry)
    forecast.process(world)

    elevated_risk = world.segments[target_seg].forecast_15m_risk
    assert elevated_risk > 0.60, f"Expected risk to rise significantly before gridlock, got {elevated_risk}"
    assert world.segments[target_seg].risk_level in ["high", "critical"]
    print(f"PASS: Early Warning Verified - Risk surged to {elevated_risk} while speed is still 40.0 km/h.")


def test_incident_corroboration_and_edge_cost():
    """
    Assertion: CV/sensor anomaly creates candidate and raises nearby edge costs.
    """
    world = load_test_world_state()
    monitor = MonitorAgent()
    incident_agent = IncidentAgent()

    target_seg = "seg_03"
    seg = world.segments[target_seg]

    # Baseline cost
    cost_before, _ = RouteCostPolicy.calculate_edge_cost(seg)

    # Telemetry with speed collapse and CV detection
    incident_telemetry = {
        target_seg: {
            "speed": 6.0,
            "occupancy": 0.95,
            "sensor_anomaly": True,
            "cv_evidence": {
                "camera_id": "CAM_CENTRAL_03",
                "frame_id": "frm_083012_hd",
                "detected_class": "collision",
                "confidence": 0.94,
                "bounding_box": [120, 180, 480, 560],
                "timestamp": "08:30:12"
            }
        }
    }

    monitor.process(world, telemetry_update=incident_telemetry)
    incident_agent.process(world, telemetry_update=incident_telemetry)

    # Assert incident candidate created
    assert len(world.incidents) == 1, "Expected 1 incident candidate"
    inc = world.incidents[0]
    assert inc.location_segment_id == target_seg
    assert inc.type == "collision"
    assert inc.confidence >= 0.90
    assert inc.severity == "critical"
    assert "evidence_svg" in inc.evidence

    # Assert edge cost on target segment escalated
    cost_after, breakdown = RouteCostPolicy.calculate_edge_cost(seg)
    assert cost_after > cost_before * 10, f"Expected cost to rise drastically, before: {cost_before}, after: {cost_after}"
    assert breakdown["incident_penalty_sec"] > 0
    print(f"PASS: Incident Corroboration Verified - Cost rose from {cost_before}s to {cost_after}s.")


if __name__ == "__main__":
    test_forecast_early_warning()
    test_incident_corroboration_and_edge_cost()
    print("All Phase 2 Intelligence tests PASSED successfully!")
