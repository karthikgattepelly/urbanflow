export interface RoadSegment {
  id: string;
  name: string;
  start_node: string;
  end_node: string;
  length_km: number;
  speed_limit_kmh: number;
  current_speed: number;
  baseline_speed: number;
  occupancy: number;
  baseline_occupancy: number;
  forecast_15m_risk: number;
  forecast_30m_risk: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  coordinates: [number, number][];
  status: 'normal' | 'congested' | 'blocked' | 'priority_corridor';
  incident_id?: string;
}

export interface CVEvidence {
  camera_id: string;
  frame_id: string;
  detected_class: string;
  confidence: number;
  bounding_box?: number[];
  timestamp: string;
  evidence_svg?: string;
}

export interface Incident {
  id: string;
  type: 'stopped_vehicle' | 'collision' | 'heavy_congestion' | 'debris' | 'roadwork';
  location_segment_id: string;
  location_name: string;
  coordinates: [number, number];
  confidence: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'cleared' | 'monitoring';
  evidence: {
    sensor_anomaly?: string;
    speed_detected?: number;
    occupancy?: number;
    cv_corroborated?: boolean;
    camera_id?: string;
    frame_id?: string;
    detected_class?: string;
    cv_confidence?: number;
    bounding_box?: number[];
    evidence_svg?: string;
  };
  timestamp: string;
}

export interface EmergencyRequest {
  id: string;
  vehicle_id: string;
  vehicle_type: 'ambulance' | 'fire_truck' | 'police';
  origin_node: string;
  destination_node: string;
  eta_target_seconds: number;
  current_eta_seconds: number;
  baseline_eta_seconds: number;
  priority: 'high' | 'critical';
  status: 'pending' | 'active' | 'completed';
  corridor_segment_ids: string[];
  priority_intersections: string[];
}

export interface RouteOption {
  id: string;
  name: string;
  segment_ids: string[];
  node_ids: string[];
  coordinates: [number, number][];
  total_distance_km: number;
  estimated_time_seconds: number;
  baseline_time_seconds: number;
  time_savings_seconds: number;
  total_cost: number;
  is_active: boolean;
  color: string;
}

export interface Recommendation {
  id: string;
  action: string;
  affected_segments: string[];
  alternatives: string[];
  expected_impact: string;
  rationale: string;
  confidence: number;
  timestamp: string;
  confirmed: boolean;
}

export interface AgentEvent {
  event_id: string;
  agent_name: string;
  timestamp: string;
  input_summary: string;
  decision: string;
  handoff_to: string;
  metadata: Record<string, any>;
}

export interface NetworkMetrics {
  average_speed_kmh: number;
  average_occupancy: number;
  network_health_score: number;
  active_alerts_count: number;
  emergency_corridor_active: boolean;
  total_active_incidents: number;
}

export interface WorldState {
  timestamp: string;
  scenario_id: string;
  step: number;
  segments: Record<string, RoadSegment>;
  incidents: Incident[];
  active_emergency?: EmergencyRequest | null;
  active_routes: Record<string, RouteOption>;
  active_recommendations: Recommendation[];
  agent_event_log: AgentEvent[];
  network_metrics: NetworkMetrics;
}
