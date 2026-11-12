import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import folium
from streamlit_folium import st_folium
from contract import make_fake_state

st.set_page_config(page_title="UrbanFlow AI", layout="wide")
st.title("🚦 UrbanFlow AI")

# ---- Initial state (kept between button clicks) ----
def init_state():
    s = make_fake_state()
    s["incidents"] = []
    s["edge_state"]["B-C"]["blocked"] = False
    s["edge_state"]["B-C"]["speed"] = 30
    s["agent_log"] = [
        {"agent": "Monitor", "msg": "Traffic normal. Watching all roads."}
    ]
    st.session_state.state = s
    st.session_state.ambulance_route = None

if "state" not in st.session_state:
    init_state()

state = st.session_state.state

nodes = {
    "A": (17.4400, 78.3489),
    "B": (17.4450, 78.3560),
    "C": (17.4500, 78.3650),
    "D": (17.4550, 78.3720),
}

# ---- Buttons ----
b1, b2, b3 = st.columns(3)

if b1.button("🚧 Simulate accident"):
    state["edge_state"]["B-C"]["blocked"] = True
    state["edge_state"]["B-C"]["speed"] = 5
    state["incidents"] = [
        {"id": 1, "edge": "B-C", "type": "accident", "severity": "high"}
    ]
    state["agent_log"].append(
        {"agent": "Incident", "msg": "Accident detected on B-C. Road blocked."})
    state["agent_log"].append(
        {"agent": "Routing", "msg": "Rerouting regular traffic away from B-C."})

if b2.button("🚑 Dispatch ambulance"):
    st.session_state.ambulance_route = ["A", "B", "C", "D"]
    state["agent_log"].append(
        {"agent": "Emergency", "msg": "Ambulance dispatched A to D. Priority route computed."})
    state["agent_log"].append(
        {"agent": "Coordinator", "msg": "Clearing path for ambulance. Signals set to green."})

if b3.button("🔄 Reset"):
    init_state()
    st.rerun()

# ---- Layout ----
col1, col2 = st.columns([2, 1])

with col1:
    m = folium.Map(location=[17.4475, 78.3600], zoom_start=15)
    for edge_id, info in state["edge_state"].items():
        u, v = edge_id.split("-")
        if info["blocked"]:
            color = "red"
        elif info["predicted_speed"] < 30:
            color = "orange"
        else:
            color = "green"
        folium.PolyLine([nodes[u], nodes[v]], color=color, weight=6,
                        tooltip=f"{edge_id}: {info['speed']} km/h").add_to(m)

    route = st.session_state.get("ambulance_route")
    if route:
        folium.PolyLine([nodes[n] for n in route], color="blue",
                        weight=10, opacity=0.6,
                        tooltip="Ambulance route").add_to(m)
    st_folium(m, width=700, height=500, returned_objects=[])

with col2:
    st.subheader("Incidents")
    if not state["incidents"]:
        st.success("No active incidents")
    for inc in state["incidents"]:
        st.error(f"{inc['type'].title()} on {inc['edge']} ({inc['severity']})")
    st.subheader("Agent log")
    for entry in reversed(state["agent_log"]):
        st.write(f"**{entry['agent']}**: {entry['msg']}")