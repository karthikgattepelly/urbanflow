import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import folium
from streamlit_folium import st_folium
from contract import make_fake_state

st.set_page_config(page_title="UrbanFlow AI", layout="wide")
st.title("🚦 UrbanFlow AI")

state = make_fake_state()

# Fake node coordinates (Hyderabad area) - replace with real graph later
nodes = {
    "A": (17.4400, 78.3489),
    "B": (17.4450, 78.3560),
    "C": (17.4500, 78.3650),
    "D": (17.4550, 78.3720),
}

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
    st_folium(m, width=700, height=500)

with col2:
    st.subheader("Incidents")
    for inc in state["incidents"]:
        st.error(f"{inc['type'].title()} on {inc['edge']} ({inc['severity']})")
    st.subheader("Agent log")
    for entry in state["agent_log"]:
        st.write(f"**{entry['agent']}**: {entry['msg']}")