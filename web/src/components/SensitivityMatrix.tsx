import type { TurnReport } from '../types';

const TRACKED_METRICS = [
  { key: 'oil_price', label: 'Oil Price', normalize: (v: number) => v / 200 },
  { key: 'escalation_level', label: 'Escalation', normalize: (v: number) => v / 10 },
] as const;

interface MetricRow {
  label: string;
  values: number[];
}

export function SensitivityMatrix({ turns }: { turns: TurnReport[] }) {
  if (turns.length < 3) return null;

  // Compute turn-over-turn volatility for oil and escalation
  const rows: MetricRow[] = TRACKED_METRICS.map(m => ({
    label: m.label,
    values: turns.map(t => m.normalize(t[m.key])),
  }));

  // Also track action intensity by agent (top 6 most active)
  const agentActivity: Record<string, number[]> = {};
  for (const t of turns) {
    for (const a of t.actions) {
      if (a.action.action_type === 'hold' || a.action.action_type === 'public_statement') continue;
      if (!agentActivity[a.agent_id]) agentActivity[a.agent_id] = new Array(turns.length).fill(0);
      const idx = turns.indexOf(t);
      agentActivity[a.agent_id][idx] += a.action.intensity;
    }
  }

  const topAgents = Object.entries(agentActivity)
    .map(([id, vals]) => ({ id, total: vals.reduce((s, v) => s + v, 0), vals }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 6);

  const AGENT_SHORT: Record<string, string> = {
    iran_composite: 'Iran', irgc_military: 'IRGC', us_trump: 'Trump',
    pentagon: 'Pentagon', israel: 'Israel', idf: 'IDF', houthis: 'Houthis',
    hezbollah: 'Hezb.', china: 'China', russia: 'Russia',
  };

  for (const agent of topAgents) {
    const maxVal = Math.max(...agent.vals, 0.01);
    rows.push({
      label: AGENT_SHORT[agent.id] || agent.id,
      values: agent.vals.map(v => v / maxVal),
    });
  }

  const maxTurn = turns.length;
  const cellWidth = Math.max(4, Math.min(12, 600 / maxTurn));

  return (
    <div className="bg-bg-card border border-border rounded-lg p-4">
      <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Activity Heatmap</h3>
      <div className="overflow-x-auto">
        <div className="min-w-fit">
          {rows.map((row) => (
            <div key={row.label} className="flex items-center gap-1 mb-0.5">
              <div className="w-16 text-[9px] text-text-muted truncate text-right pr-1 shrink-0">
                {row.label}
              </div>
              <div className="flex">
                {row.values.map((v, i) => (
                  <div
                    key={i}
                    style={{
                      width: cellWidth,
                      height: 14,
                      background: `rgba(88, 166, 255, ${Math.min(1, v) * 0.8})`,
                    }}
                    className="rounded-[1px]"
                    title={`Turn ${turns[i]?.turn}: ${v.toFixed(2)}`}
                  />
                ))}
              </div>
            </div>
          ))}
          {/* Turn axis */}
          <div className="flex items-center gap-1 mt-1">
            <div className="w-16 shrink-0" />
            <div className="flex">
              {turns.map((t, i) => (
                <div
                  key={i}
                  style={{ width: cellWidth }}
                  className="text-[7px] text-text-muted text-center"
                >
                  {i % Math.ceil(maxTurn / 10) === 0 ? t.turn : ''}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
