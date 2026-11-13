import React, { useState, useEffect, useCallback } from 'react';
import { WorldState, RoadSegment, Incident } from './types/urbanflow';
import { Header } from './components/Header';
import { TrafficMap } from './components/TrafficMap';
import { AlertRail } from './components/AlertRail';
import { RoutePanel } from './components/RoutePanel';
import { EmergencyCard } from './components/EmergencyCard';
import { DecisionDrawer } from './components/DecisionDrawer';
import { ScenarioControls } from './components/ScenarioControls';
import { X, Video, ShieldCheck, Activity } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';
const WS_URL = 'ws://127.0.0.1:8000/events';

export const App: React.FC = () => {
  const [worldState, setWorldState] = useState<WorldState | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [selectedSegment, setSelectedSegment] = useState<RoadSegment | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string>('primary');
  const [inspectingCameraIncident, setInspectingCameraIncident] = useState<Incident | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch initial world state
  const fetchState = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/network/state`);
      if (res.ok) {
        const data = await res.json();
        setWorldState(data);
      }
    } catch (err) {
      console.warn('Initial fetch error, waiting for API server...', err);
    }
  }, []);

  // Connect WebSocket
  useEffect(() => {
    fetchState();

    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWs = () => {
      try {
        socket = new WebSocket(WS_URL);

        socket.onopen = () => {
          setIsConnected(true);
        };

        socket.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'INITIAL_STATE' || msg.type === 'STATE_UPDATE') {
              setWorldState(msg.data);
            }
          } catch (e) {
            console.error('WS parse error', e);
          }
        };

        socket.onclose = () => {
          setIsConnected(false);
          reconnectTimeout = setTimeout(connectWs, 2000);
        };

        socket.onerror = () => {
          socket?.close();
        };
      } catch (e) {
        reconnectTimeout = setTimeout(connectWs, 2000);
      }
    };

    connectWs();

    return () => {
      if (socket) socket.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [fetchState]);

  // Scenario Handlers
  const handlePlayScenario = async (scenarioId: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/scenario/${scenarioId}/play`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setWorldState(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStepScenario = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/scenario/step`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setWorldState(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/scenario/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: 'normal' })
      });
      if (res.ok) {
        const data = await res.json();
        setWorldState(data);
        setSelectedSegment(null);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInjectIncident = async () => {
    setIsLoading(true);
    try {
      await fetch(`${API_BASE}/incidents/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segment_id: 'seg_03', incident_type: 'collision' })
      });
      await fetchState();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDispatchAmbulance = async () => {
    setIsLoading(true);
    try {
      await fetch(`${API_BASE}/emergencies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vehicle_id: 'AMB-104',
          vehicle_type: 'ambulance',
          origin_node: 'N_WEST_GATE',
          destination_node: 'N_HOSPITAL_PLAZA',
          priority: 'critical'
        })
      });
      await fetchState();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmRecommendation = async (recId: string) => {
    try {
      await fetch(`${API_BASE}/recommendations/${recId}/confirm`, { method: 'POST' });
      await fetchState();
    } catch (e) {
      console.error(e);
    }
  };

  if (!worldState) {
    return (
      <div className="min-h-screen bg-[#090D16] flex flex-col items-center justify-center p-6 text-center">
        <Activity className="w-12 h-12 text-blue-500 animate-spin mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Connecting to UrbanFlow AI Command Center...</h2>
        <p className="text-sm text-slate-400 font-mono">Initializing shared world state & WebSocket stream</p>
      </div>
    );
  }

  const latestRec = worldState.active_recommendations[0] || null;

  return (
    <div className="min-h-screen bg-[#090D16] text-slate-100 flex flex-col">
      {/* 1. Header Bar */}
      <Header
        metrics={worldState.network_metrics}
        scenarioId={worldState.scenario_id}
        step={worldState.step}
        isConnected={isConnected}
      />

      {/* Main Command Center Layout */}
      <main className="flex-1 p-6 space-y-6 max-w-[1720px] w-full mx-auto">
        {/* 2. Interactive Scenario Controls */}
        <ScenarioControls
          currentScenario={worldState.scenario_id}
          step={worldState.step}
          onPlayScenario={handlePlayScenario}
          onStepScenario={handleStepScenario}
          onReset={handleReset}
          onInjectIncident={handleInjectIncident}
          onDispatchAmbulance={handleDispatchAmbulance}
          isLoading={isLoading}
        />

        {/* 3. Core Operational Split Screen */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[580px]">
          {/* Left Column: Map & Active Emergency Banner (8 Cols) */}
          <div className="lg:col-span-8 flex flex-col space-y-4">
            {/* Active Emergency Banner */}
            <EmergencyCard emergency={worldState.active_emergency} />

            {/* Central Leaflet Road Network Map */}
            <div className="flex-1 min-h-[460px] relative">
              <TrafficMap
                segments={worldState.segments}
                incidents={worldState.incidents}
                activeRoutes={worldState.active_routes}
                activeEmergency={worldState.active_emergency}
                selectedSegmentId={selectedSegment?.id}
                onSelectSegment={(seg) => setSelectedSegment(seg)}
              />
            </div>
          </div>

          {/* Right Column: Alert Rail & Route Optimizer (4 Cols) */}
          <div className="lg:col-span-4 flex flex-col space-y-4">
            {/* Live Alert Rail */}
            <div className="h-[280px]">
              <AlertRail
                incidents={worldState.incidents}
                onInspectCamera={(inc) => setInspectingCameraIncident(inc)}
              />
            </div>

            {/* Dynamic Route Optimizer Cards */}
            <div className="flex-1 min-h-[260px]">
              <RoutePanel
                routes={worldState.active_routes}
                selectedRouteId={selectedRouteId}
                onSelectRoute={(id) => setSelectedRouteId(id)}
              />
            </div>
          </div>
        </div>

        {/* 4. Operator Decision Drawer ("Why this action?") */}
        <div className="pt-2">
          <DecisionDrawer
            recommendation={latestRec}
            agentTimeline={worldState.agent_event_log}
            onConfirmRecommendation={handleConfirmRecommendation}
          />
        </div>
      </main>

      {/* CCTV Camera Modal Dialog */}
      {inspectingCameraIncident && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0B1120] border border-slate-700 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Video className="w-5 h-5 text-red-500" />
                <h3 className="text-sm font-bold text-white uppercase font-mono tracking-wider">
                  Roadside CCTV Inspection Frame
                </h3>
              </div>
              <button
                onClick={() => setInspectingCameraIncident(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950 p-2 shadow-inner">
              <div
                className="w-full h-80"
                dangerouslySetInnerHTML={{ __html: inspectingCameraIncident.evidence?.evidence_svg || '' }}
              />
            </div>

            <div className="grid grid-cols-3 gap-3 text-xs font-mono bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-slate-300">
              <div>
                <span className="text-slate-500 block uppercase text-[10px]">Camera Unit</span>
                <span className="font-bold text-white">{inspectingCameraIncident.evidence?.camera_id}</span>
              </div>
              <div>
                <span className="text-slate-500 block uppercase text-[10px]">Classification</span>
                <span className="font-bold text-red-400 uppercase">{inspectingCameraIncident.type}</span>
              </div>
              <div>
                <span className="text-slate-500 block uppercase text-[10px]">Confidence</span>
                <span className="font-bold text-emerald-400">{Math.round(inspectingCameraIncident.confidence * 100)}%</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

