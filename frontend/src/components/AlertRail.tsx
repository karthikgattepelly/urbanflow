import React from 'react';
import { Incident } from '../types/urbanflow';
import { AlertCircle, Camera, CheckCircle, Video, Eye } from 'lucide-react';

interface AlertRailProps {
  incidents: Incident[];
  onAcknowledge?: (incidentId: string) => void;
  onInspectCamera?: (incident: Incident) => void;
}

export const AlertRail: React.FC<AlertRailProps> = ({
  incidents,
  onAcknowledge,
  onInspectCamera
}) => {
  const activeIncidents = incidents.filter(i => i.status === 'active');

  return (
    <div className="bg-[#0B1120] border border-slate-800 rounded-xl p-4 flex flex-col h-full shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">Live Incidents & Alerts</h2>
        </div>
        <span className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700">
          {activeIncidents.length} Active
        </span>
      </div>

      <div className="overflow-y-auto space-y-3 flex-1 pr-1">
        {activeIncidents.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center text-center p-4 text-slate-500">
            <CheckCircle className="w-8 h-8 text-emerald-500/40 mb-2" />
            <p className="text-xs font-medium">All corridors clear</p>
            <p className="text-[11px] text-slate-600 mt-0.5">No unacknowledged incidents detected</p>
          </div>
        ) : (
          activeIncidents.map((inc) => {
            const hasSvg = !!inc.evidence?.evidence_svg;

            return (
              <div
                key={inc.id}
                className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition-all shadow-md group"
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded ${
                        inc.severity === 'critical'
                          ? 'bg-red-950 text-red-400 border border-red-800'
                          : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}>
                        {inc.severity}
                      </span>
                      <span className="text-xs font-bold text-white capitalize">
                        {inc.type.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1 font-medium">
                      {inc.location_name}
                    </div>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">{inc.timestamp}</span>
                </div>

                {/* Evidence Metrics */}
                <div className="grid grid-cols-2 gap-2 my-2.5 text-[11px] font-mono bg-slate-950/70 p-2 rounded border border-slate-800/60">
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">Confidence</span>
                    <span className="text-emerald-400 font-bold">{Math.round(inc.confidence * 100)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">Sensor Speed</span>
                    <span className="text-red-400 font-bold">{inc.evidence?.speed_detected || 5} km/h</span>
                  </div>
                  <div className="col-span-2 pt-1 border-t border-slate-800/60 flex items-center justify-between text-slate-400 text-[10px]">
                    <span className="flex items-center gap-1">
                      <Camera className="w-3 h-3 text-cyan-400" />
                      {inc.evidence?.camera_id || 'CCTV CH-04'}
                    </span>
                    <span className="text-cyan-400 font-semibold">CV Verified</span>
                  </div>
                </div>

                {/* CCTV Frame Thumbnail Preview */}
                {hasSvg && (
                  <div className="my-2 rounded border border-slate-800 overflow-hidden bg-slate-950/80 p-1">
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1 px-1">
                      <span className="flex items-center gap-1"><Video className="w-3 h-3 text-red-500" /> CCTV Evidence</span>
                      <span>{inc.evidence?.frame_id}</span>
                    </div>
                    <div
                      className="w-full h-24 overflow-hidden rounded cursor-pointer"
                      onClick={() => onInspectCamera && onInspectCamera(inc)}
                      dangerouslySetInnerHTML={{ __html: inc.evidence.evidence_svg || '' }}
                    />
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-end gap-2 mt-3 pt-2 border-t border-slate-800/60">
                  {hasSvg && (
                    <button
                      onClick={() => onInspectCamera && onInspectCamera(inc)}
                      className="flex items-center gap-1 text-[11px] font-medium text-cyan-400 hover:text-cyan-300 px-2 py-1 rounded bg-slate-800/60 border border-slate-700/60"
                    >
                      <Eye className="w-3 h-3" /> View Frame
                    </button>
                  )}
                  <button
                    onClick={() => onAcknowledge && onAcknowledge(inc.id)}
                    className="text-[11px] font-semibold text-white bg-blue-600 hover:bg-blue-500 px-2.5 py-1 rounded shadow-sm shadow-blue-600/30 transition-all"
                  >
                    Acknowledge
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

