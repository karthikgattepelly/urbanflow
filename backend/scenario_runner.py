"""
UrbanFlow AI - Scenario Runner
Executes deterministic scenario playback (normal, forecast, blockage, emergency)
and drives the Coordinator Agent loop with live WebSocket broadcasting.
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path
from shared.schemas import RoadSegment, EmergencyRequest
from shared.world_state import WorldState
from agents.coordinator_agent import CoordinatorAgent


class ScenarioRunner:
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.world_state: WorldState = WorldState()
        self.graph_data: Dict[str, Any] = {}
        self.fixtures_data: Dict[str, Any] = {}
        self.current_scenario_id: str = "normal"
        self.current_step_index: int = 0
        self.is_playing: bool = False

        self.load_data()
        self.reset_to_scenario("normal")

    def load_data(self):
        base_dir = Path(__file__).parent.parent / "data"
        with open(base_dir / "district_graph.json", "r") as f:
            self.graph_data = json.load(f)
        with open(base_dir / "telemetry_fixtures.json", "r") as f:
            self.fixtures_data = json.load(f)

    def reset_to_scenario(self, scenario_id: str = "normal") -> WorldState:
        """
        Resets canonical world state to nominal baseline using district_graph.json.
        """
        self.current_scenario_id = scenario_id
        self.current_step_index = 0
        self.is_playing = False

        self.world_state = WorldState(scenario_id=scenario_id, step=0)

        # Populate road segments from graph
        for seg_dict in self.graph_data.get("segments", []):
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
            self.world_state.segments[segment.id] = segment

        # Run an initial coordinator cycle to establish baseline routes & metrics
        self.coordinator.process(self.world_state)
        return self.world_state

    def step_scenario(self, scenario_id: Optional[str] = None) -> WorldState:
        """
        Steps forward in the selected scenario using fixture data.
        """
        if scenario_id and scenario_id != self.current_scenario_id:
            self.current_scenario_id = scenario_id
            self.current_step_index = 0

        scenarios = self.fixtures_data.get("scenarios", {})
        scenario_def = scenarios.get(self.current_scenario_id, {})
        steps = scenario_def.get("steps", [])

        if not steps:
            # Fallback coordinator step if no steps defined
            self.coordinator.process(self.world_state)
            return self.world_state

        # Bound step index
        if self.current_step_index >= len(steps):
            self.current_step_index = len(steps) - 1

        step_data = steps[self.current_step_index]
        telemetry_update = step_data.get("telemetry", {})

        # Check for emergency request in fixture
        emg_req_dict = step_data.get("emergency_request")
        emg_req: Optional[EmergencyRequest] = None
        if emg_req_dict:
            emg_req = EmergencyRequest(
                id=emg_req_dict["id"],
                vehicle_id=emg_req_dict["vehicle_id"],
                vehicle_type=emg_req_dict.get("vehicle_type", "ambulance"),
                origin_node=emg_req_dict["origin_node"],
                destination_node=emg_req_dict["destination_node"],
                eta_target_seconds=emg_req_dict.get("eta_target_seconds", 360.0),
                current_eta_seconds=0.0,
                baseline_eta_seconds=0.0,
                priority=emg_req_dict.get("priority", "critical"),
                status="active"
            )

        # Drive coordinator cycle
        self.coordinator.process(
            self.world_state,
            telemetry_update=telemetry_update,
            emergency_request=emg_req
        )

        # Advance step for next tick
        if self.current_step_index < len(steps) - 1:
            self.current_step_index += 1

        return self.world_state

    def play_scenario(self, scenario_id: str) -> WorldState:
        """
        Fast-forwards through all steps of the selected scenario to reach target state.
        """
        self.reset_to_scenario(scenario_id)
        scenarios = self.fixtures_data.get("scenarios", {})
        steps = scenarios.get(scenario_id, {}).get("steps", [])

        for i in range(len(steps)):
            self.current_step_index = i
            self.step_scenario(scenario_id)

        return self.world_state

    def inject_incident(
        self,
        segment_id: str,
        incident_type: str = "collision"
    ) -> WorldState:
        """
        Manually injects an incident on any segment for interactive operator drills.
        """
        telemetry_update = {
            segment_id: {
                "speed": 5.0,
                "occupancy": 0.96,
                "sensor_anomaly": True,
                "cv_evidence": {
                    "camera_id": f"CAM_{segment_id.upper()}",
                    "frame_id": f"frm_manual_{segment_id}",
                    "detected_class": incident_type,
                    "confidence": 0.95,
                    "bounding_box": [120, 180, 480, 560],
                    "timestamp": "Manual Drill"
                }
            }
        }
        self.coordinator.process(self.world_state, telemetry_update=telemetry_update)
        return self.world_state

    def dispatch_emergency(
        self,
        vehicle_id: str = "AMB-104",
        origin_node: str = "N_WEST_GATE",
        destination_node: str = "N_HOSPITAL_PLAZA"
    ) -> WorldState:
        """
        Dispatches an emergency vehicle unit and initiates priority corridor optimization.
        """
        emg = EmergencyRequest(
            id=f"emg_{vehicle_id.lower().replace('-', '_')}",
            vehicle_id=vehicle_id,
            vehicle_type="ambulance",
            origin_node=origin_node,
            destination_node=destination_node,
            eta_target_seconds=360.0,
            current_eta_seconds=0.0,
            baseline_eta_seconds=0.0,
            priority="critical",
            status="active"
        )
        self.coordinator.process(self.world_state, emergency_request=emg)
        return self.world_state

    def approve_recommendation(self, rec_id: str) -> WorldState:
        """
        Marks an operator recommendation as confirmed/approved.
        """
        for rec in self.world_state.active_recommendations:
            if rec.id == rec_id:
                rec.confirmed = True
        return self.world_state


# Global singleton instance
runner = ScenarioRunner()

