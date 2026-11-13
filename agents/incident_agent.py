"""
UrbanFlow AI - Incident Agent
Input: Sensor anomalies from MonitorAgent + CCTV camera CV frames
Output: Corroborated incident candidates with verified evidence, confidence, and severity
"""

from typing import Dict, Any, List, Optional
import time
from agents.base_agent import BaseAgent
from shared.world_state import WorldState
from shared.schemas import AgentEvent, Incident, CVEvidence
from models.cv_adapter import CVAdapter


class IncidentAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="IncidentAgent")

    def process(
        self,
        world_state: WorldState,
        telemetry_update: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentEvent:
        """
        Corroborates sensor anomalies against roadside CCTV computer vision observations.
        Promotes corroborated anomalies to active Incidents.
        """
        # Retrieve recent anomaly events from the audit log
        latest_monitor_event = next(
            (e for e in reversed(world_state.agent_event_log) if e.agent_name == "MonitorAgent"),
            None
        )
        anomalies = latest_monitor_event.metadata.get("anomalies", []) if latest_monitor_event else []

        new_incidents: List[Incident] = []

        # Check telemetry for CV evidence on any segment
        telemetry_data = telemetry_update or {}

        # 1. Process segments with both sensor anomalies and/or CV evidence
        candidate_seg_ids = set([a["segment_id"] for a in anomalies] + list(telemetry_data.keys()))

        for seg_id in candidate_seg_ids:
            if seg_id not in world_state.segments:
                continue

            segment = world_state.segments[seg_id]
            reading = telemetry_data.get(seg_id, {})
            cv_raw = reading.get("cv_evidence")

            # Check if this segment already has an active incident
            existing_incident = next((i for i in world_state.incidents if i.location_segment_id == seg_id and i.status == "active"), None)

            # Determine if sensor anomaly exists for this segment
            sensor_anomaly = next((a for a in anomalies if a["segment_id"] == seg_id), None)

            # Parse CV evidence if available
            cv_evidence: Optional[CVEvidence] = None
            if cv_raw:
                cv_evidence = CVAdapter.parse_detection_evidence(
                    segment_id=seg_id,
                    raw_evidence=cv_raw,
                    timestamp=time.strftime("%H:%M:%S", time.gmtime())
                )

            # Evidence fusion logic
            if sensor_anomaly or cv_evidence:
                # Fused confidence calculation
                sensor_conf = sensor_anomaly["score"] if sensor_anomaly else 0.40
                cv_conf = cv_evidence.confidence if cv_evidence else 0.0

                if sensor_anomaly and cv_evidence:
                    # Multi-sensor corroboration boosts confidence
                    fused_conf = min(0.99, round(1.0 - (1.0 - sensor_conf) * (1.0 - cv_conf), 2))
                else:
                    fused_conf = round(sensor_conf if sensor_anomaly else cv_conf, 2)

                # Classify type & severity
                incident_type = cv_evidence.detected_class if cv_evidence else "heavy_congestion"
                if incident_type in ["collision", "stopped_vehicle"]:
                    severity = "critical" if incident_type == "collision" else "high"
                    segment_status = "blocked"
                else:
                    severity = "medium"
                    segment_status = "congested"

                # Midpoint coordinate for pin placement
                coords = segment.coordinates[len(segment.coordinates) // 2]

                evidence_dict = {
                    "sensor_anomaly": sensor_anomaly["reason"] if sensor_anomaly else "sensor_speed_decay",
                    "speed_detected": segment.current_speed,
                    "occupancy": segment.occupancy,
                    "cv_corroborated": bool(cv_evidence),
                }

                if cv_evidence:
                    evidence_dict.update({
                        "camera_id": cv_evidence.camera_id,
                        "frame_id": cv_evidence.frame_id,
                        "detected_class": cv_evidence.detected_class,
                        "cv_confidence": cv_evidence.confidence,
                        "bounding_box": cv_evidence.bounding_box,
                        "evidence_svg": CVAdapter.generate_evidence_svg(cv_evidence)
                    })

                if existing_incident:
                    # Update existing incident
                    existing_incident.confidence = fused_conf
                    existing_incident.severity = severity
                    existing_incident.evidence.update(evidence_dict)
                    existing_incident.status = "active"
                    segment.status = segment_status
                    segment.incident_id = existing_incident.id
                else:
                    incident = Incident(
                        id=f"inc_{len(world_state.incidents) + 1:03d}",
                        type=incident_type,
                        location_segment_id=seg_id,
                        location_name=segment.name,
                        coordinates=coords,
                        confidence=fused_conf,
                        severity=severity,
                        status="active",
                        evidence=evidence_dict,
                        timestamp=time.strftime("%H:%M:%S", time.gmtime())
                    )
                    world_state.incidents.append(incident)
                    new_incidents.append(incident)
                    segment.status = segment_status
                    segment.incident_id = incident.id

        world_state.recalculate_metrics()

        if new_incidents:
            decision = (
                f"Verified {len(new_incidents)} active incident(s): "
                + ", ".join(f"{i.id} on {i.location_name} ({i.type}, conf: {int(i.confidence * 100)}%, severity: {i.severity})" for i in new_incidents)
                + ". Raised affected corridor edge costs."
            )
        else:
            decision = f"Zero unconfirmed incidents. Active incident count: {len(world_state.incidents)}."

        event = world_state.add_agent_event(
            agent_name=self.name,
            input_summary=f"Evaluated {len(anomalies)} sensor anomalies and CV camera streams.",
            decision=decision,
            handoff_to="RoutingAgent",
            metadata={
                "verified_incidents": [i.model_dump() for i in new_incidents]
            }
        )
        return event

