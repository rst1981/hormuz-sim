import { useState } from 'react';
import { useSimulationStore } from '../stores/simulationStore';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { colors, FACTION_COLORS } from '../theme';
import type { AgentState } from '../types';
import { ResetButton } from '../components/ResetButton';

const BELIEF_DISPLAY = [
  'iran_missile_stocks', 'israel_interceptor_stocks', 'irgc_cohesion',
  'us_political_will', 'regime_survival_prob', 'ceasefire_probability',
  'uprising_intensity', 'iran_nuclear_progress',
];

export function AgentExplorerPage() {
  const { simState, reset } = useSimulationStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const agents = simState?.agents ?? {};
  const agentList = Object.values(agents);
  const selected = selectedId ? agents[selectedId] : null;

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Agent Explorer</h2>
        <ResetButton onClick={reset} label="New Sim" />
      </div>
      <div className="flex gap-4 flex-1 min-h-0">
      {/* Agent List */}
      <div className="w-64 flex-shrink-0 bg-bg-card border border-border rounded-lg overflow-auto">
        <div className="p-3 border-b border-border">
          <h3 className="text-xs uppercase tracking-wider text-text-muted">Agents ({agentList.length})</h3>
        </div>
        {agentList.map(a => (
          <button
            key={a.agent_id}
            onClick={() => setSelectedId(a.agent_id)}
            className={`w-full text-left px-3 py-2 text-sm border-b border-border transition-colors ${
              selectedId === a.agent_id ? 'bg-bg-hover text-text-accent' : 'text-text-primary hover:bg-bg-hover'
            }`}
          >
            <div className="font-medium text-xs">{a.name}</div>
            <div className="text-[10px] text-text-muted">{a.type} · p(v)={a.p_victory.toFixed(2)}</div>
          </button>
        ))}
      </div>

      {/* Detail */}
      <div className="flex-1 space-y-4 overflow-auto">
        {selected ? (
          <AgentDetail agent={selected} />
        ) : (
          <div className="flex items-center justify-center h-full text-text-muted text-sm">
            Select an agent to explore
          </div>
        )}
      </div>
      </div>
    </div>
  );
}

function AgentDetail({ agent }: { agent: AgentState }) {
  const radarData = BELIEF_DISPLAY.map(key => {
    const belief = agent.beliefs[key];
    return { var: key.replace(/_/g, ' ').slice(0, 15), value: belief?.mean ?? 0.5 };
  });

  return (
    <>
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold">{agent.name}</h2>
            <span className="text-xs text-text-muted">{agent.type} · {agent.agent_id}</span>
          </div>
          <div className="text-right">
            <div className="text-2xl font-mono font-bold" style={{ color: agent.p_victory > 0.5 ? colors.outcomes.ceasefire : colors.chart.escalation }}>
              {(agent.p_victory * 100).toFixed(0)}%
            </div>
            <div className="text-[10px] text-text-muted">P(Victory)</div>
          </div>
        </div>

        {/* Type-specific info */}
        {agent.current_mode && (
          <div className="text-xs mb-2">
            Trump Mode: <span className="font-mono font-semibold" style={{ color: colors.trump[agent.current_mode as keyof typeof colors.trump] || '#8b949e' }}>
              {agent.current_mode.toUpperCase()}
            </span> (turn {agent.turns_in_mode})
          </div>
        )}
        {agent.ripeness !== undefined && (
          <div className="text-xs mb-2">Ripeness: <span className="font-mono">{agent.ripeness.toFixed(2)}</span></div>
        )}
        {agent.accumulated_cost !== undefined && (
          <div className="text-xs mb-2">Accumulated Cost: <span className="font-mono">{agent.accumulated_cost.toFixed(3)}</span></div>
        )}
      </div>

      {/* Belief Radar */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Belief Radar</h3>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#21262d" />
            <PolarAngleAxis dataKey="var" tick={{ fontSize: 8, fill: '#8b949e' }} />
            <PolarRadiusAxis domain={[0, 1]} tick={{ fontSize: 8, fill: '#8b949e' }} />
            <Radar dataKey="value" stroke={colors.chart.coalition} fill={colors.chart.coalition} fillOpacity={0.3} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Factions (Iran Composite) */}
      {agent.factions && (
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Faction Power</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={agent.factions.map(f => ({
              name: f.name, influence: +(f.influence * 100).toFixed(1),
              fill: FACTION_COLORS[f.faction_id.includes('hardline') ? 'hardliners' : f.faction_id.includes('pragm') ? 'pragmatists' : f.faction_id.includes('civil') || f.faction_id.includes('fm') ? 'civilian' : 'succession'] || colors.text.muted,
            }))}>
              <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#8b949e' }} />
              <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} unit="%" />
              <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
              <Bar dataKey="influence" radius={[4, 4, 0, 0]}>
                {agent.factions.map((f, i) => {
                  const fColor = f.hardline_score > 0.6 ? FACTION_COLORS.hardliners : f.hardline_score < 0.3 ? FACTION_COLORS.civilian : FACTION_COLORS.pragmatists;
                  return <Bar key={i} dataKey="influence" fill={fColor} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="text-xs text-text-muted mt-2">
            Dominant: <span className="text-text-accent">{agent.dominant_faction}</span> · Mode: {agent.resolution_mode}
          </div>
        </div>
      )}
    </>
  );
}
