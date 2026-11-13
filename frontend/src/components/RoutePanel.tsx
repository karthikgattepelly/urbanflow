import React from 'react';
import { RouteOption } from '../types/urbanflow';
import { Navigation, Clock, TrendingUp, CheckCircle2 } from 'lucide-react';

interface RoutePanelProps {
  routes: Record<string, RouteOption>;
  selectedRouteId?: string;
  onSelectRoute?: (routeId: string) => void;
}

export const RoutePanel: React.FC<RoutePanelProps> = ({
  routes,
  selectedRouteId = 'primary',
  onSelectRoute
}) => {
  const routeEntries = Object.entries(routes);

  return (
    <div className="bg-[#0B1120] border border-slate-800 rounded-xl p-4 flex flex-col h-full shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">Dynamic Route Optimization</h2>
        </div>
        <span className="text-xs font-mono text-slate-400">Dijkstra / A* Live</span>
      </div>

      <div className="space-y-3 overflow-y-auto flex-1 pr-1">
        {routeEntries.length === 0 ? (
          <div className="text-xs text-slate-500 text-center py-8 font-mono">No active routes computed</div>
        ) : (
          routeEntries.map(([key, route]) => {
            const isCorridor = key === 'emergency_corridor';
            const isSelected = selectedRouteId === key;

            return (
              <div
                key={key}
                onClick={() => onSelectRoute && onSelectRoute(key)}
                className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
                  isCorridor
                    ? 'bg-emerald-950/30 border-emerald-700/60 shadow-lg shadow-emerald-950/20'
                    : isSelected
                    ? 'bg-slate-900/90 border-blue-500 shadow-md'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Route Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: route.color || (isCorridor ? '#10B981' : '#3B82F6') }}
                    />
                    <span className="text-xs font-bold text-white tracking-tight">{route.name}</span>
                  </div>
                  {isCorridor && (
                    <span className="bg-emerald-950 text-emerald-400 border border-emerald-700/60 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full">
                      Priority Corridor
                    </span>
                  )}
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-3 gap-2 my-2 text-center">
                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800/50">
                    <span className="text-[9px] uppercase font-mono text-slate-500 block">ETA</span>
                    <span className="text-sm font-bold font-mono text-white">
                      {Math.round(route.estimated_time_seconds / 60 * 10) / 10} <span className="text-[10px] font-normal text-slate-400">min</span>
                    </span>
                  </div>

                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800/50">
                    <span className="text-[9px] uppercase font-mono text-slate-500 block">Distance</span>
                    <span className="text-sm font-bold font-mono text-slate-200">
                      {route.total_distance_km} <span className="text-[10px] font-normal text-slate-400">km</span>
                    </span>
                  </div>

                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800/50">
                    <span className="text-[9px] uppercase font-mono text-slate-500 block">Time Delta</span>
                    <span className={`text-sm font-bold font-mono ${route.time_savings_seconds > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                      {route.time_savings_seconds > 0
                        ? `-${Math.round(route.time_savings_seconds / 60 * 10) / 10}m`
                        : `${Math.round(route.baseline_time_seconds / 60 * 10) / 10}m`}
                    </span>
                  </div>
                </div>

                {/* Segments Path Badges */}
                <div className="mt-2 text-[10px] font-mono text-slate-400 flex flex-wrap gap-1 items-center">
                  <span className="text-slate-500">Path:</span>
                  {route.segment_ids.map((sid, idx) => (
                    <React.Fragment key={sid}>
                      <span className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700/60">
                        {sid}
                      </span>
                      {idx < route.segment_ids.length - 1 && <span className="text-slate-600">→</span>}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

