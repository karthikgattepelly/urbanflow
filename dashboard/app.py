import sys, os, math, random
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import folium
import networkx as nx
import osmnx as ox
from streamlit_folium import st_folium

st.set_page_config(page_title="UrbanFlow AI", layout="wide")
st.title("🚦 UrbanFlow AI")

ROOT = os.path.dirname(os.path.dirname(__file__))
GRAPH_PATH = os.path.join(ROOT, "data", "graph.graphml")


@st.cache_resource
def load():
    G = ox.load_graphml(GRAPH_PATH)
    try:
        G = ox.truncate.largest_component(G, strongly=True)
    except Exception:
        pass
    edges = []
    for u, v, d in G.edges(data=True):
        if "geometry" in d:
            pts = [(y, x) for x, y in d["geometry"].coords]
        else:
            pts = [(G.nodes[u]["y"], G.nodes[u]["x"]),
                   (G.nodes[v]["y"], G.nodes[v]["x"])]
        edges.append((u, v, pts))
    return G, edges


G, EDGES = load()
CENTER = (17.4400, 78.3489)
SRC = ox.distance.nearest_nodes(G, X=CENTER[1] - 0.008, Y=CENTER[0] - 0.007)
DST = ox.distance.nearest_nodes(G, X=CENTER[1] + 0.008, Y=CENTER[0] + 0.007)


def dist_m(a, b):
    la1, lo1 = math.radians(G.nodes[a]["y"]), math.radians(G.nodes[a]["x"])
    la2, lo2 = math.radians(G.nodes[b]["y"]), math.radians(G.nodes[b]["x"])
    h = math.sin((la2 - la1) / 2) ** 2 + \
        math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def make_weight(emergency):
    def w(u, v, d):
        if (u, v) in st.session_state.blocked:
            return None  # None = edge is hidden from the search
        f = 1.0 if emergency else st.session_state.congestion.get((u, v), 1.0)
        best = None
        for e in d.values():
            spd = float(e.get("speed_kph", 30)) * f
            t = float(e.get("length", 1)) / (max(spd, 3) / 3.6)
            if best is None or t < best:
                best = t
        return best
    return w


def route(src, dst, emergency):
    w = make_weight(emergency)
    try:
        path = nx.astar_path(G, src, dst,
                             heuristic=lambda a, b: dist_m(a, b) / 33.0,
                             weight=w)
    except nx.NetworkXNoPath:
        return None, None
    secs = sum(w(a, b, G[a][b]) for a, b in zip(path, path[1:]))
    return path, secs


def init_state():
    rng = random.Random(42)
    cong = {}
    for u, v, _ in EDGES:
        if rng.random() < 0.15:
            cong[(u, v)] = rng.uniform(0.35, 0.65)   # congested
        else:
            cong[(u, v)] = rng.uniform(0.8, 1.0)     # flowing
    st.session_state.congestion = cong
    st.session_state.blocked = set()
    st.session_state.incidents = []
    st.session_state.amb = None
    st.session_state.reg = None
    st.session_state.eta = None
    st.session_state.log = [("Monitor", "Traffic normal. Watching all roads.")]


def log(agent, msg):
    st.session_state.log.append((agent, msg))


def plan():
    amb, t1 = route(SRC, DST, True)
    reg, t2 = route(SRC, DST, False)
    st.session_state.amb, st.session_state.reg = amb, reg
    st.session_state.eta = (t1, t2)


if "congestion" not in st.session_state:
    init_state()

# ---------------- Buttons ----------------
b1, b2, b3, b4 = st.columns(4)

if b1.button("📈 Forecast +30 min"):
    rng = random.Random()
    n = 0
    for k in list(st.session_state.congestion):
        if rng.random() < 0.10:
            st.session_state.congestion[k] *= 0.7
            n += 1
    log("Monitor", f"Forecast: congestion rising on {n} road segments in the next 30 min.")

if b2.button("🚧 Simulate accident"):
    if st.session_state.incidents:
        st.warning("An accident is already active.")
    else:
        base, _ = route(SRC, DST, True)
        a, b = base[len(base) // 2], base[len(base) // 2 + 1]
        st.session_state.blocked.add((a, b))
        if G.has_edge(b, a):
            st.session_state.blocked.add((b, a))
        st.session_state.incidents.append(
            {"type": "accident", "severity": "high", "nodes": (a, b)})
        log("Incident", "Accident detected on the main corridor. Road blocked.")
        log("Routing", "Rerouting regular traffic around the blocked road.")
        if st.session_state.amb:
            plan()

if b3.button("🚑 Dispatch ambulance"):
    plan()
    t1, t2 = st.session_state.eta
    log("Emergency", f"Ambulance dispatched. Priority route ETA {t1/60:.1f} min.")
    log("Coordinator",
        f"Signals cleared for ambulance. Regular traffic ETA {t2/60:.1f} min on its own route.")

if b4.button("🔄 Reset"):
    init_state()
    st.rerun()

# ---------------- Layout ----------------
col1, col2 = st.columns([2, 1])

with col1:
    m = folium.Map(location=CENTER, zoom_start=15)
    groups = {"green": [], "orange": [], "red": []}
    blocked_lines = []
    for u, v, pts in EDGES:
        if (u, v) in st.session_state.blocked:
            blocked_lines.append(pts)
            continue
        f = st.session_state.congestion[(u, v)]
        key = "green" if f > 0.7 else "orange" if f > 0.45 else "red"
        groups[key].append(pts)
    for color, lines in groups.items():
        if lines:
            folium.PolyLine(lines, color=color, weight=3, opacity=0.8).add_to(m)
    if blocked_lines:
        folium.PolyLine(blocked_lines, color="black", weight=9,
                        tooltip="BLOCKED: accident").add_to(m)

    def coords(path):
        return [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]

    if st.session_state.reg:
        folium.PolyLine(coords(st.session_state.reg), color="purple", weight=5,
                        dash_array="8", tooltip="Regular traffic route").add_to(m)
    if st.session_state.amb:
        folium.PolyLine(coords(st.session_state.amb), color="blue", weight=8,
                        opacity=0.8, tooltip="Ambulance priority route").add_to(m)

    folium.Marker(coords([SRC])[0], tooltip="Ambulance start",
                  icon=folium.Icon(color="blue", icon="ambulance", prefix="fa")).add_to(m)
    folium.Marker(coords([DST])[0], tooltip="Hospital",
                  icon=folium.Icon(color="red", icon="plus", prefix="fa")).add_to(m)

    st_folium(m, width=900, height=550, returned_objects=[])
    st.caption("Green = flowing, orange = slow, red = congested, black = blocked. "
               "Blue = ambulance route, purple dashed = regular traffic route.")

with col2:
    st.subheader("Incidents")
    if not st.session_state.incidents:
        st.success("No active incidents")
    for inc in st.session_state.incidents:
        st.error(f"{inc['type'].title()} ({inc['severity']})")

    if st.session_state.eta:
        t1, t2 = st.session_state.eta
        c1, c2 = st.columns(2)
        c1.metric("Ambulance ETA", f"{t1/60:.1f} min")
        c2.metric("Regular ETA", f"{t2/60:.1f} min")

    st.subheader("Agent log")
    for agent, msg in reversed(st.session_state.log):
        st.write(f"**{agent}**: {msg}")