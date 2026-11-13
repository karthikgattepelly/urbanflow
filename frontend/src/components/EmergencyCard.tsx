import React from 'react';
import { EmergencyRequest } from '../types/urbanflow';
import { Siren, Clock, ShieldAlert, ArrowRight, Zap } from 'lucide-react';

interface EmergencyCardProps {
  emergency?: EmergencyRequest | null;
}

export const EmergencyCard: React.FC<EmergencyCardProps> = ({ emergency }) => {
  if (!emergency || emergency.status !== 'active') {
    return (
      <div className="bg-[#0B1120] border border-slate-800 rounded-xl p-4 shadow-lg flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
            <Siren className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-400 font-mono uppercase">Emergency Priority Transit</div>
            <div className="text-[11px] text-slate-500">No active priority dispatch. Corridor signals in standard timing.</div>
          </div>
        </div>
        <span className="text-[10px] font-mono bg-slate-900 text-slate-500 border border-slate-800 px-2.5 py-1 rounded">
          STANDBY
        </span>
      </div>
    );
  }

  const timeSavedMin = Math.max(0, Math.round((emergency.baseline_eta_seconds - emergency.current_eta_seconds) / 60 * 10) / 10);
  const currentEtaMin = Math.round(emergency.current_eta_seconds / 60 * 10) / 10;
  const targetEtaMin = Math.round(emergency.eta_target_seconds / 60);

  return (
    <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900/90 to-slate-900 border border-emerald-600/50 rounded-xl p-4 shadow-xl relative overflow-hidden">
      {/* Glow highlight */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none"></div>

      <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-md shadow-emerald-500/20">
            <Siren className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white font-mono">{emergency.vehicle_id}</span>
              <span className="text-[10px] font-mono font-bold bg-emerald-900 text-emerald-300 border border-emerald-700/60 px-2 py-0.5 rounded-full uppercase">
                {emergency.priority} PRIORITY
              </span>
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5 font-mono">
              <span>{emergency.origin_node}</span>
              <ArrowRight className="w-3 h-3 text-emerald-400" />
              <span className="text-white font-bold">{emergency.destination_node}</span>
            </div>
          </div>
        </div>

        {/* ETA Display */}
        <div className="flex items-center gap-3">
          <div className="bg-slate-950/80 border border-slate-800 px-3 py-1.5 rounded-lg text-right">
            <span className="text-[9px] uppercase font-mono text-slate-500 block">Corridor ETA</span>
            <div className="text-lg font-bold font-mono text-emerald-400 leading-none">
              {currentEtaMin} <span className="text-xs font-normal text-slate-400">min</span>
            </div>
          </div>
          <div className="bg-emerald-950/70 border border-emerald-800/80 px-3 py-1.5 rounded-lg text-right">
            <span className="text-[9px] uppercase font-mono text-emerald-400 block">Time Saved</span>
            <div className="text-lg font-bold font-mono text-emerald-300 leading-none">
              -{timeSavedMin} <span className="text-xs font-normal text-emerald-400">min</span>
            </div>
          </div>
        </div>
      </div>

      {/* Pre-empted Signal Intersections */}
      <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
        <div className="flex items-center gap-2 text-slate-400">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-400 font-semibold">Pre-empted Green Wave Signals:</span>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {emergency.priority_intersections.length === 0 ? (
            <span className="text-slate-500 text-[11px]">Direct priority corridor lock</span>
          ) : (
            emergency.priority_intersections.map((nodeId) => (
              <span
                key={nodeId}
                className="bg-emerald-950 text-emerald-300 border border-emerald-700/60 text-[10px] px-2 py-0.5 rounded font-mono flex items-center gap-1"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                {nodeId}
              </span>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

