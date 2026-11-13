import React, { useState } from 'react';
import { Recommendation, AgentEvent } from '../types/urbanflow';
import { HelpCircle, ChevronDown, ChevronUp, CheckCircle, ShieldCheck, Clock, ArrowRight, FileText } from 'lucide-react';

interface DecisionDrawerProps {
  recommendation?: Recommendation | null;
  agentTimeline: AgentEvent[];
  onConfirmRecommendation?: (recId: string) => void;
}

export const DecisionDrawer: React.FC<DecisionDrawerProps> = ({
  recommendation,
  agentTimeline,
  onConfirmRecommendation
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<'rationale' | 'timeline'>('rationale');

  if (!recommendation) {
    return null;
  }

  return (
    <div className="bg-[#0B1120] border border-slate-800 rounded-xl overflow-hidden shadow-2xl transition-all">
      {/* Header bar / Toggle */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="px-4 py-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between cursor-pointer hover:bg-slate-800/80 transition-all select-none"
      >
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-md bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
            <HelpCircle className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                Operator Decision Drawer: Why this action?
              </span>
              <span className="text-[10px] font-mono bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 rounded">
                Confidence {Math.round(recommendation.confidence * 100)}%
              </span>
              {recommendation.confirmed && (
                <span className="text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-700 px-2 py-0.5 rounded flex items-center gap-1 font-semibold">
                  <CheckCircle className="w-3 h-3 text-emerald-400" /> Confirmed by Operator
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-400 font-medium truncate max-w-xl">
              {recommendation.action}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </div>

      {/* Content when open */}
      {isOpen && (
        <div className="p-4 space-y-4">
          {/* Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-mono">
            <button
              onClick={() => setActiveTab('rationale')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === 'rationale'
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              Operational Rationale & Trade-offs
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === 'timeline'
                  ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              Multi-Agent Audit Trail ({agentTimeline.length} Events)
            </button>
          </div>

          {activeTab === 'rationale' ? (
            <div className="space-y-4 text-xs">
              {/* Action Headline & Impact */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3">
                <div className="text-[10px] font-mono uppercase text-slate-400 font-semibold mb-1">Recommended Action</div>
                <div className="text-sm font-bold text-white mb-2">{recommendation.action}</div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800/80 text-[11px] font-mono text-emerald-400">
                  <span className="text-slate-400 font-bold block mb-0.5 uppercase text-[9px]">Projected Outcome:</span>
                  {recommendation.expected_impact}
                </div>
              </div>

              {/* Formatted Rationale Narrative */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-3 space-y-2 text-slate-300 leading-relaxed font-sans">
                <div className="text-[10px] font-mono uppercase text-slate-400 font-semibold mb-2">Decision Synthesis</div>
                {recommendation.rationale.split('\n\n').map((paragraph, idx) => {
                  return (
                    <div key={idx} className="text-[12px] text-slate-300">
                      <span dangerouslySetInnerHTML={{ __html: paragraph.replace(/\*\*(.*?)\*\*/g, '<b class="text-white font-mono">$1</b>') }} />
                    </div>
                  );
                })}
              </div>

              {/* Trade-offs & Alternatives Considered */}
              {recommendation.alternatives.length > 0 && (
                <div className="bg-slate-900/50 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-[10px] font-mono uppercase text-slate-400 font-semibold mb-1.5">Alternatives Evaluated & Rejected</div>
                  <ul className="space-y-1.5 font-mono text-[11px] text-slate-400">
                    {recommendation.alternatives.map((alt, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-red-400 font-bold">✕</span>
                        <span>{alt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Operator Confirmation Button */}
              <div className="flex items-center justify-between pt-2">
                <div className="text-[11px] text-slate-500 font-mono">
                  Human-in-the-loop: Severe signal preemption requires operator authorization.
                </div>
                {!recommendation.confirmed ? (
                  <button
                    onClick={() => onConfirmRecommendation && onConfirmRecommendation(recommendation.id)}
                    className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-4 py-2 rounded-lg text-xs font-mono shadow-md shadow-emerald-600/30 transition-all"
                  >
                    <CheckCircle className="w-4 h-4" /> Authorize & Confirm Plan
                  </button>
                ) : (
                  <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950 border border-emerald-700 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4" /> Plan Approved & Enforced
                  </span>
                )}
              </div>
            </div>
          ) : (
            /* Multi-Agent Audit Timeline */
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {agentTimeline.map((evt, idx) => (
                <div
                  key={evt.event_id || idx}
                  className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2.5 font-mono text-xs flex items-start justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                        {evt.agent_name}
                      </span>
                      <span className="text-[10px] text-slate-500">{evt.timestamp}</span>
                      <span className="text-slate-600">→</span>
                      <span className="text-[10px] text-slate-400 font-semibold">{evt.handoff_to}</span>
                    </div>
                    <div className="text-[11px] text-white font-medium pl-1">
                      {evt.decision}
                    </div>
                    <div className="text-[10px] text-slate-500 pl-1">
                      Input: {evt.input_summary}
                    </div>
                  </div>
                  <span className="text-[9px] text-slate-600 shrink-0">{evt.event_id}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

