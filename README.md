# UrbanFlow AI — Adaptive Traffic Intelligence & Emergency Response

> An observable, closed-loop urban operations command center: **Sense $\to$ Predict $\to$ Decide $\to$ Act $\to$ Explain**.

---

## 1. System Architecture

UrbanFlow AI enforces an **event-driven shared canonical world model** where agents never store private truths!:

```
[Road Sensors + CCTV Cameras]
               │
               ▼
        ┌──────────────┐
        │ MonitorAgent │ ─── Telemetry normalization & sensor anomaly scoring
        └──────────────┘
               │ (MonitorEvent)
               ▼
        ┌───────────────┐
        │ ForecastAgent │ ─── 15m/30m predictive congestion risk before speed collapse
        └───────────────┘
               │ (ForecastEvent)
               ▼
        ┌───────────────┐
        │ IncidentAgent │ ─── Multi-source corroboration (Sensors + CCTV Computer Vision)
        └───────────────┘
               │ (IncidentEvent)
               ▼
        ┌──────────────┐
        │ RoutingAgent │ ─── Dynamic Dijkstra / A* graph routing around blockages
        └──────────────┘
               │ (RouteEvent)
               ▼
        ┌────────────────┐
        │ EmergencyAgent │ ─── Priority corridor reservation & green-wave signal preemption
        └────────────────┘
               │ (EmergencyEvent)
               ▼
        ┌──────────────────┐
        │ ExplanationAgent │ ─── Operator narrative: What changed, Why now, Trade-offs
        └──────────────────┘
               │ (DecisionEvent)
               ▼
        ┌──────────────────┐
        │ CoordinatorAgent │ ─── Publishes canonical snapshot to UI & WebSockets
        └──────────────────┘
```

---

## 2. Dynamic Route Cost Policy

$$\text{edge\_cost} = \text{base\_travel\_time} \times \text{congestion\_multiplier} + \text{incident\_penalty} + \text{reliability\_penalty}$$

* **Congestion Multiplier**: Evaluates velocity ratio and occupancy pressure. Siren escort absorbs 65% of congestion delay.
* **Incident Penalty**: Applied when an active physical collision or blockage is confirmed (+9999s penalty forces rerouting).
* **Reliability Penalty**: Penalizes corridors predicted to collapse within 15 minutes, directing traffic to stable bypasses.

---

## 3. The 4 Deterministic Scenarios

| Scenario | Trigger / Input | System Response |
| :--- | :--- | :--- |
| **1. Steady Flow** | Nominal speeds (45–58 km/h), occupancy < 30% | Green map, nominal routes, health score 95% |
| **2. 15m Forecast Risk** | Inflow surge on `seg_03` ($d\text{Occ}/dt > +0.15/\text{min}$) | Risk jumps to **Critical** 15m *before* speed collapses |
| **3. Collision Blockage** | Speed collapses to 6 km/h, verified by CCTV camera `CAM_CENTRAL_03` | Status = `blocked`, edge cost jumps $81\text{s} \to 10,569\text{s}$, traffic rerouted |
| **4. Ambulance Dispatch** | Critical dispatch for `AMB-104` from West Gate to Hospital | Pre-empts signals at 3 intersections, saves **100s** vs. unoptimized baseline |

---

## 4. How to Run the Application

### Option A: Complete All-in-One Command Center (Recommended)
Launch the FastAPI backend server (which automatically serves the compiled React dashboard at `http://127.0.0.1:8000/`):

```powershell
# From the root directory:
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

### Option B: Frontend Hot-Reloading Development Mode
```powershell
# Terminal 1: Backend
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

# Terminal 2: React Vite Dev Server
cd frontend
npm run dev
```
Open **[http://localhost:5173/](http://localhost:5173/)** in your browser.

---

## 5. Running the Test Suite

Execute the 8 integration tests validating all 5 required acceptance criteria:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -s
```

All 8 tests pass in ~1 second with comprehensive proof output.

