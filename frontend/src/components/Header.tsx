import React from 'react';
import { NetworkMetrics } from '../types/urbanflow';
import { Activity, AlertTriangle, ShieldCheck, Siren, Gauge, Radio } from 'lucide-react';

interface HeaderProps {
  metrics: NetworkMetrics;
  scenarioId: string;
  step: number;
  isConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  metrics,
  scenarioId,
  step,
  isConnected
}) => {
  const getScenarioBadge = () => {
    switch (scenarioId) {
      case 'forecast':
        return <span className="bg-amber-950/80 text-amber-400 border border-amber-700/50 px-2.5 py-1 rounded-md text-xs font-semibold tracking-wide uppercase">15m Risk Forecast</span>;
      case 'blockage':
        return <span className="bg-red-950/80 text-red-400 border border-red-700/50 px-2.5 py-1 rounded-md text-xs font-semibold tracking-wide uppercase">Incident / Blockage</span>;
      case 'emergency':
        return <span className="bg-emerald-950/80 text-emerald-400 border border-emerald-700/50 px-2.5 py-1 rounded-md text-xs font-semibold tracking-wide uppercase flex items-center gap-1.5"><Siren className="w-3.5 h-3.5 animate-pulse text-emerald-400" /> Emergency Corridor</span>;
      default:
        return <span className="bg-blue-950/80 text-blue-400 border border-blue-700/50 px-2.5 py-1 rounded-md text-xs font-semibold tracking-wide uppercase">Steady Flow</span>;
    }
  };

  return (
    <header className="bg-[#0B1120] border-b border-slate-800 px-6 py-3 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-50 shadow-lg">
      {/* Brand Title */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center shadow-md shadow-blue-500/20">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-white tracking-tight">UrbanFlow AI</h1>
            <span className="text-[10px] font-mono bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700">v1.0.0</span>
            {getScenarioBadge()}
          </div>
          <p className="text-xs text-slate-400">Adaptive Traffic Intelligence & Emergency Command Center</p>
        </div>
      </div>

      {/* Real-time Telemetry Metrics Bar */}
      <div className="flex items-center gap-6">
        {/* Network Health Score */}
        <div className="flex items-center gap-2.5 bg-slate-900/90 border border-slate-800/80 px-3.5 py-1.5 rounded-lg">
          <ShieldCheck className={`w-4 h-4 ${metrics.network_health_score >= 80 ? 'text-emerald-400' : metrics.network_health_score >= 50 ? 'text-amber-400' : 'text-red-400'}`} />
          <div>
            <div className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Network Health</div>
            <div className="text-sm font-bold font-mono text-white leading-none">
              {metrics.network_health_score}%
            </div>
          </div>
        </div>

        {/* Average Speed */}
        <div className="flex items-center gap-2.5 bg-slate-900/90 border border-slate-800/80 px-3.5 py-1.5 rounded-lg">
          <Gauge className="w-4 h-4 text-cyan-400" />
          <div>
            <div className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Avg Speed</div>
            <div className="text-sm font-bold font-mono text-white leading-none">
              {metrics.average_speed_kmh} <span className="text-xs font-normal text-slate-400">km/h</span>
            </div>
          </div>
        </div>

        {/* Active Alerts */}
        <div className="flex items-center gap-2.5 bg-slate-900/90 border border-slate-800/80 px-3.5 py-1.5 rounded-lg">
          <AlertTriangle className={`w-4 h-4 ${metrics.active_alerts_count > 0 ? 'text-amber-400' : 'text-slate-500'}`} />
          <div>
            <div className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Alerts</div>
            <div className="text-sm font-bold font-mono text-white leading-none">
              {metrics.active_alerts_count}
            </div>
          </div>
        </div>

        {/* Emergency Count */}
        <div className="flex items-center gap-2.5 bg-slate-900/90 border border-slate-800/80 px-3.5 py-1.5 rounded-lg">
          <Siren className={`w-4 h-4 ${metrics.emergency_corridor_active ? 'text-emerald-400 animate-bounce' : 'text-slate-500'}`} />
          <div>
            <div className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">Emergency Units</div>
            <div className="text-sm font-bold font-mono text-white leading-none">
              {metrics.emergency_corridor_active ? '1 Active' : '0 Idle'}
            </div>
          </div>
        </div>

        {/* Live WebSocket Status Indicator */}
        <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 pl-2">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-red-500'}`} />
          <span>{isConnected ? 'LIVE' : 'OFFLINE'}</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-500">Step {step}</span>
        </div>
      </div>
    </header>
  );
};

