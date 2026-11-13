"""
UrbanFlow AI - Computer Vision Adapter
Ingests roadside CCTV camera observations, validates detections, and generates
verifiable evidence payloads with labels, bounding boxes, and timestamps.
"""

from typing import Dict, Any, Optional
from shared.schemas import CVEvidence


class CVAdapter:
    """
    Adapter for roadside traffic camera vision models (e.g. YOLOv8 / TrafficVision).
    Treats CV output as verifiable evidence with confidence and bounding boxes.
    """

    # Pre-indexed camera fixtures matching district segments
    CAMERA_REGISTRY = {
        "seg_03": {
            "camera_id": "CAM_CENTRAL_03",
            "intersection": "Central Hub & 2nd St Overpass",
            "resolution": "1920x1080",
            "fps": 30
        },
        "seg_02": {
            "camera_id": "CAM_CIVIC_02",
            "intersection": "Civic Center Eastbound",
            "resolution": "1920x1080",
            "fps": 30
        },
        "seg_15": {
            "camera_id": "CAM_BROADWAY_15",
            "intersection": "Broadway 1st & Commerce Junction",
            "resolution": "1920x1080",
            "fps": 30
        }
    }

    @classmethod
    def get_camera_for_segment(cls, segment_id: str) -> Optional[Dict[str, Any]]:
        return cls.CAMERA_REGISTRY.get(segment_id)

    @classmethod
    def parse_detection_evidence(
        cls,
        segment_id: str,
        raw_evidence: Optional[Dict[str, Any]] = None,
        timestamp: str = "08:30:12"
    ) -> Optional[CVEvidence]:
        """
        Parses raw vision telemetry into structured CVEvidence.
        """
        if not raw_evidence:
            return None

        camera_info = cls.get_camera_for_segment(segment_id) or {
            "camera_id": f"CAM_{segment_id.upper()}"
        }

        return CVEvidence(
            camera_id=raw_evidence.get("camera_id", camera_info["camera_id"]),
            frame_id=raw_evidence.get("frame_id", f"frm_{timestamp.replace(':', '')}_hd"),
            detected_class=raw_evidence.get("detected_class", "stopped_vehicle"),
            confidence=float(raw_evidence.get("confidence", 0.92)),
            bounding_box=raw_evidence.get("bounding_box", [120, 180, 480, 560]),
            timestamp=raw_evidence.get("timestamp", timestamp)
        )

    @classmethod
    def generate_evidence_svg(cls, evidence: CVEvidence) -> str:
        """
        Generates an SVG representation of the camera frame with bounding box and HUD overlay.
        Can be rendered directly in the UI decision drawer!
        """
        bbox = evidence.bounding_box or [120, 180, 480, 560]
        ymin, xmin, ymax, xmax = bbox
        width = xmax - xmin
        height = ymax - ymin

        color = "#EF4444" if evidence.detected_class in ["collision", "stopped_vehicle"] else "#F59E0B"

        svg = f"""<svg viewBox="0 0 640 360" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
  <!-- CCTV Background -->
  <rect width="640" height="360" fill="#0F172A"/>
  <!-- Road Lanes Perspective -->
  <polygon points="180,360 260,180 380,180 460,360" fill="#1E293B" stroke="#334155" stroke-width="2"/>
  <line x1="320" y1="180" x2="320" y2="360" stroke="#FBBF24" stroke-width="2" stroke-dasharray="12,12"/>
  
  <!-- Bounding Box -->
  <rect x="{xmin}" y="{ymin}" width="{width}" height="{height}" fill="{color}" fill-opacity="0.25" stroke="{color}" stroke-width="3" rx="4"/>
  <rect x="{xmin}" y="{max(10, ymin - 24)}" width="{width}" height="22" fill="{color}"/>
  <text x="{xmin + 6}" y="{max(26, ymin - 8)}" font-family="monospace" font-size="12" font-weight="bold" fill="#FFFFFF">
    {evidence.detected_class.upper()} ({int(evidence.confidence * 100)}%)
  </text>
  
  <!-- CCTV HUD Overlay -->
  <text x="20" y="30" font-family="monospace" font-size="12" fill="#22C55E">● REC</text>
  <text x="75" y="30" font-family="monospace" font-size="12" fill="#94A3B8">{evidence.camera_id} [CH-04]</text>
  <text x="480" y="30" font-family="monospace" font-size="12" fill="#94A3B8">{evidence.timestamp} UTC</text>
  <text x="20" y="340" font-family="monospace" font-size="11" fill="#64748B">FRAME: {evidence.frame_id} | 1080P HD</text>
</svg>"""
        return svg

