"""
UrbanFlow AI - FastAPI Application Server
Provides REST endpoints and WebSocket stream as specified in Mini PRD Section 6.
"""

from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pathlib import Path
from fastapi.staticfiles import StaticFiles

from backend.scenario_runner import runner
from backend.websocket_manager import ws_manager
from shared.schemas import EmergencyRequest, RouteOption, Recommendation, Incident

app = FastAPI(
    title="UrbanFlow AI Command Center API",
    description="Adaptive multi-agent traffic intelligence and emergency response command center.",
    version="1.0.0"
)

# Enable CORS for development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlayScenarioRequest(BaseModel):
    scenario_id: str = "emergency"


class EmergencyDispatchRequest(BaseModel):
    vehicle_id: str = "AMB-104"
    vehicle_type: str = "ambulance"
    origin_node: str = "N_WEST_GATE"
    destination_node: str = "N_HOSPITAL_PLAZA"
    priority: str = "critical"


class InjectIncidentRequest(BaseModel):
    segment_id: str = "seg_03"
    incident_type: str = "collision"


@app.get("/api/status")
def read_root():
    return {
        "system": "UrbanFlow AI",
        "status": "online",
        "scenario": runner.current_scenario_id,
        "step": runner.world_state.step,
        "health_score": runner.world_state.network_metrics.network_health_score
    }


@app.get("/network/state")
def get_network_state():
    """
    Returns full map-ready network state including segments, incidents,
    forecast risks, active routes, metrics, and latest agent events.
    """
    return runner.world_state.model_dump()


@app.post("/scenario/{scenario_id}/play")
def play_scenario(scenario_id: str):
    """
    Replays the specified scenario ('normal', 'forecast', 'blockage', 'emergency').
    """
    if scenario_id not in ["normal", "forecast", "blockage", "emergency"]:
        raise HTTPException(status_code=400, detail=f"Invalid scenario '{scenario_id}'")

    updated_state = runner.play_scenario(scenario_id)
    ws_manager.broadcast_sync({
        "type": "STATE_UPDATE",
        "data": updated_state.model_dump()
    })
    return updated_state.model_dump()


@app.post("/scenario/step")
def step_scenario():
    """
    Advances scenario playback by one step.
    """
    updated_state = runner.step_scenario()
    ws_manager.broadcast_sync({
        "type": "STATE_UPDATE",
        "data": updated_state.model_dump()
    })
    return updated_state.model_dump()


@app.post("/scenario/reset")
def reset_scenario(req: PlayScenarioRequest = PlayScenarioRequest(scenario_id="normal")):
    """
    Resets the entire simulation to baseline.
    """
    updated_state = runner.reset_to_scenario(req.scenario_id)
    ws_manager.broadcast_sync({
        "type": "STATE_UPDATE",
        "data": updated_state.model_dump()
    })
    return updated_state.model_dump()


@app.post("/emergencies")
def create_emergency(req: EmergencyDispatchRequest):
    """
    Dispatches an emergency priority vehicle and computes dedicated corridor.
    """
    updated_state = runner.dispatch_emergency(
        vehicle_id=req.vehicle_id,
        origin_node=req.origin_node,
        destination_node=req.destination_node
    )
    ws_manager.broadcast_sync({
        "type": "STATE_UPDATE",
        "data": updated_state.model_dump()
    })
    return updated_state.active_emergency.model_dump() if updated_state.active_emergency else {}


@app.get("/routes")
def get_routes():
    """
    Returns primary, alternative, and emergency priority routes with ETAs.
    """
    return {k: v.model_dump() for k, v in runner.world_state.active_routes.items()}


@app.get("/decisions/{decision_id}")
def get_decision(decision_id: str):
    """
    Returns full evidence, confidence, alternatives, and operator trade-offs for a recommendation.
    """
    for rec in runner.world_state.active_recommendations:
        if rec.id == decision_id or decision_id == "latest":
            return {
                "recommendation": rec.model_dump(),
                "agent_timeline": [
                    e.model_dump() for e in runner.world_state.agent_event_log[-8:]
                ],
                "incidents": [i.model_dump() for i in runner.world_state.incidents],
                "routes": {k: v.model_dump() for k, v in runner.world_state.active_routes.items()}
            }
    raise HTTPException(status_code=404, detail="Decision record not found")


@app.post("/incidents/inject")
def inject_incident(req: InjectIncidentRequest):
    """
    Allows manual operator injection of physical blockages for demo drills.
    """
    updated_state = runner.inject_incident(req.segment_id, req.incident_type)
    ws_manager.broadcast_sync({
        "type": "STATE_UPDATE",
        "data": updated_state.model_dump()
    })
    return {"status": "injected", "segment": req.segment_id}


@app.post("/recommendations/{rec_id}/confirm")
def confirm_recommendation(rec_id: str):
    """
    Confirms and approves an operational recommendation (Human-in-the-loop control).
    """
    updated_state = runner.approve_recommendation(rec_id)
    ws_manager.broadcast_sync({
        "type": "STATE_UPDATE",
        "data": updated_state.model_dump()
    })
    return {"status": "confirmed", "recommendation_id": rec_id}


@app.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    """
    Real-time push WebSocket for live dashboard updates, agent timeline events, and alert broadcasts.
    """
    await ws_manager.connect(websocket)
    # Immediately send current state on connection
    await websocket.send_json({
        "type": "INITIAL_STATE",
        "data": runner.world_state.model_dump()
    })
    try:
        while True:
            client_msg = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# Mount static compiled frontend command center if built
dist_path = Path(__file__).parent.parent / "frontend" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")

