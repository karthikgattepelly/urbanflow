def make_fake_state():
    return {
        "edge_state": {
            "A-B": {"speed": 40, "predicted_speed": 25, "blocked": False},
            "B-C": {"speed": 10, "predicted_speed": 8, "blocked": True},
            "C-D": {"speed": 35, "predicted_speed": 30, "blocked": False},
        },
        "incidents": [
            {"id": 1, "edge": "B-C", "type": "accident", "severity": "high"}
        ],
        "agent_log": [
            {"agent": "Monitor", "msg": "Congestion rising on A-B"},
            {"agent": "Incident", "msg": "Accident detected on B-C"},
        ],
    }