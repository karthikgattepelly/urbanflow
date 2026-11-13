"""
snap_to_roads.py

Replaces the hand-typed 3-point `coordinates` of every segment in
data/district_graph.json with real street geometry from the public OSRM
routing service, so lines follow actual roads on the map.

Run from the project root (needs internet, no extra packages):
    python data/snap_to_roads.py

A backup is saved to data/district_graph.backup.json first.
Set UPDATE_LENGTHS = True to also replace length_km with the real road
distance (this changes ETAs, so re-run the tests afterwards).
"""
import json
import shutil
import time
import urllib.request
from pathlib import Path

GRAPH_PATH = Path("data/district_graph.json")
BACKUP_PATH = Path("data/district_graph.backup.json")
OSRM = "https://router.project-osrm.org"
UPDATE_LENGTHS = False


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "urbanflow-hackathon/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def snap_node(lat: float, lng: float) -> tuple[float, float]:
    """Move a point onto the nearest real road. Returns (lat, lng)."""
    data = get_json(f"{OSRM}/nearest/v1/driving/{lng},{lat}?number=1")
    lon, la = data["waypoints"][0]["location"]
    return la, lon


def road_geometry(a: tuple[float, float], b: tuple[float, float]):
    """Real road path between two (lat, lng) points. Returns (coords, km)."""
    url = (
        f"{OSRM}/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}"
        "?overview=full&geometries=geojson&steps=false"
    )
    data = get_json(url)
    route = data["routes"][0]
    # GeoJSON is [lng, lat]; Leaflet and our JSON use [lat, lng]
    coords = [[round(lat, 6), round(lng, 6)] for lng, lat in route["geometry"]["coordinates"]]
    return coords, route["distance"] / 1000.0


def main() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    shutil.copyfile(GRAPH_PATH, BACKUP_PATH)
    print(f"Backup saved to {BACKUP_PATH}")

    # 1. Snap every node onto a road once, so segments sharing a node join up
    snapped = {}
    for node in graph["nodes"]:
        lat, lng = snap_node(node["lat"], node["lng"])
        snapped[node["id"]] = (lat, lng)
        node["lat"], node["lng"] = round(lat, 6), round(lng, 6)
        print(f"node {node['id']:<20} -> {lat:.5f}, {lng:.5f}")
        time.sleep(0.3)

    # 2. Replace each segment's coordinates with the real road path
    for seg in graph["segments"]:
        a, b = snapped[seg["start_node"]], snapped[seg["end_node"]]
        try:
            coords, km = road_geometry(a, b)
        except Exception as exc:  # keep old coords if one request fails
            print(f"{seg['id']}: FAILED ({exc}), keeping old coordinates")
            continue
        seg["coordinates"] = coords
        if UPDATE_LENGTHS:
            seg["length_km"] = round(km, 3)
        print(f"{seg['id']}: {len(coords)} points, {km:.2f} km (old length {seg['length_km']} km)")
        time.sleep(0.3)

    GRAPH_PATH.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    print("Done. Restart the backend so it loads the new file.")


if __name__ == "__main__":
    main()
