import React from 'react';
import { Play, RotateCcw, StepForward, AlertOctagon, Siren, BarChart2, Shield } from 'lucide-react';

interface ScenarioControlsProps {
  currentScenario: string;
  step: number;
  onPlayScenario: (scenarioId: string) => void;
  onStepScenario: () => void;
  onReset: () => void;
  onInjectIncident: () => void;
  onDispatchAmbulance: () => void;
  isLoading?: boolean;
}

export const ScenarioControls: React.FC<ScenarioControlsProps> = ({
  currentScenario,
  step,
  onPlayScenario,
  onStepScenario,
  onReset,
  onInjectIncident,
  onDispatchAmbulance,
  isLoading = false
}) => {
  return (
    <div className="bg-[#0B1120] border border-slate-800 rounded-xl p-4 shadow-lg flex flex-wrap items-center justify-between gap-4">
      {/* 4 Core Deterministic Scenarios */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-mono uppercase text-slate-500 font-bold mr-1">Scenarios:</span>
        
        {/* Normal */}
        <button
          onClick={() => onPlayScenario('normal')}
          disabled={isLoading}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
            currentScenario === 'normal'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 border border-blue-500'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <Shield className="w-3.5 h-3.5" /> 1. Steady Flow
        </button>

        {/* Forecast */}
        <button
          onClick={() => onPlayScenario('forecast')}
          disabled={isLoading}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
            currentScenario === 'forecast'
              ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30 border border-amber-500'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <BarChart2 className="w-3.5 h-3.5" /> 2. 15m Risk Forecast
        </button>

        {/* Blockage */}
        <button
          onClick={() => onPlayScenario('blockage')}
          disabled={isLoading}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
            currentScenario === 'blockage'
              ? 'bg-red-600 text-white shadow-md shadow-red-600/30 border border-red-500'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <AlertOctagon className="w-3.5 h-3.5" /> 3. Collision Blockage
        </button>

        {/* Emergency */}
        <button
          onClick={() => onPlayScenario('emergency')}
          disabled={isLoading}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all flex items-center gap-1.5 ${
            currentScenario === 'emergency'
              ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30 border border-emerald-500'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <Siren className="w-3.5 h-3.5" /> 4. Ambulance Dispatch
        </button>
      </div>

      {/* Playback Controls & Action Injections */}
      <div className="flex items-center gap-2">
        <button
          onClick={onStepScenario}
          disabled={isLoading}
          className="bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold flex items-center gap-1.5 transition-all"
        >
          <StepForward className="w-3.5 h-3.5 text-cyan-400" /> Step Tick
        </button>

        <button
          onClick={onReset}
          disabled={isLoading}
          className="bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700/80 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold flex items-center gap-1.5 transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5 text-amber-400" /> Reset
        </button>

        <div className="h-4 w-px bg-slate-800 mx-1"></div>

        <button
          onClick={onInjectIncident}
          disabled={isLoading}
          className="bg-red-950/80 hover:bg-red-900 text-red-300 border border-red-800/80 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold flex items-center gap-1.5 transition-all"
        >
          <AlertOctagon className="w-3.5 h-3.5 text-red-400" /> Drill: Inject Collision
        </button>

        <button
          onClick={onDispatchAmbulance}
          disabled={isLoading}
          className="bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-800/80 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold flex items-center gap-1.5 transition-all"
        >
          <Siren className="w-3.5 h-3.5 text-emerald-400" /> Drill: AMB-104
        </button>
      </div>
    </div>
  );
};

