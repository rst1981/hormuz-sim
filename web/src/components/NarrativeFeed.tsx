import type { TurnReport } from '../types';

const ACTION_TEMPLATES: Record<string, (agentId: string, target: string | null, intensity: number) => string> = {
  missile_strike: (a, t, i) => `${agentName(a)} launched ${i > 0.7 ? 'a massive' : 'a limited'} missile strike${t ? ` against ${t}` : ''}.`,
  drone_strike: (a, t, i) => `${agentName(a)} deployed ${i > 0.6 ? 'swarms of' : ''} attack drones${t ? ` targeting ${t}` : ''}.`,
  cyber_attack: (a, t) => `${agentName(a)} executed a cyber operation${t ? ` against ${t} infrastructure` : ''}.`,
  naval_interdiction: (a, t) => `${agentName(a)} began interdicting shipping${t ? ` near ${t}` : ' in the Gulf'}.`,
  strait_mining: (a) => `${agentName(a)} deployed mines in the Strait of Hormuz, threatening global oil transit.`,
  air_strike: (a, t, i) => `${agentName(a)} conducted ${i > 0.7 ? 'intensive' : 'precision'} air strikes${t ? ` on ${t}` : ''}.`,
  escalate: (a, _, i) => `${agentName(a)} escalated tensions${i > 0.7 ? ' dramatically' : ''}.`,
  de_escalate: (a) => `${agentName(a)} signaled willingness to de-escalate.`,
  negotiate: (a, t) => `${agentName(a)} opened ${t ? `negotiations with ${t}` : 'back-channel talks'}.`,
  sanction: (a, t) => `${agentName(a)} imposed new sanctions${t ? ` on ${t}` : ''}.`,
  proxy_activation: (a) => `${agentName(a)} activated proxy forces across the region.`,
  public_statement: (a) => `${agentName(a)} issued a public statement.`,
  hold: (a) => `${agentName(a)} maintained current posture.`,
  nuclear_advance: (a) => `${agentName(a)} accelerated nuclear enrichment activities.`,
  spr_release: (a) => `${agentName(a)} authorized a Strategic Petroleum Reserve release.`,
  diplomatic_pressure: (a, t) => `${agentName(a)} applied diplomatic pressure${t ? ` on ${t}` : ''}.`,
};

const AGENT_NAMES: Record<string, string> = {
  iran_composite: 'Tehran',
  irgc_military: 'IRGC Command',
  us_trump: 'The White House',
  pentagon: 'The Pentagon',
  israel: 'Jerusalem',
  idf: 'The IDF',
  china: 'Beijing',
  india: 'New Delhi',
  russia: 'Moscow',
  turkey: 'Ankara',
  saudi: 'Riyadh',
  uae: 'Abu Dhabi',
  bahrain_kuwait: 'Bahrain-Kuwait',
  houthis: 'Ansar Allah',
  kh_pmf: 'Iraqi militias',
  hezbollah: 'Hezbollah',
  pkk_pjak: 'PKK/PJAK',
  uprising: 'Iranian protesters',
};

function agentName(id: string): string {
  return AGENT_NAMES[id] || id;
}

function narrateTurn(turn: TurnReport): string[] {
  const lines: string[] = [];

  lines.push(`**Day ${turn.day}** — Turn ${turn.turn}`);

  // Random events first (these are big)
  for (const ev of turn.random_events) {
    lines.push(`🔥 **${ev.name}**: ${ev.description}`);
  }

  // Significant actions (skip holds and public_statements)
  const significant = turn.actions.filter(
    a => a.action.action_type !== 'hold' && a.action.action_type !== 'public_statement'
  );

  for (const a of significant.slice(0, 6)) {
    const template = ACTION_TEMPLATES[a.action.action_type];
    if (template) {
      lines.push(template(a.agent_id, a.action.target, a.action.intensity));
    } else {
      lines.push(`${agentName(a.agent_id)}: ${a.action.description || a.action.action_type}`);
    }
  }

  // Miscalculations
  for (const m of turn.miscalculation_events) {
    lines.push(`⚠️ **MISCALCULATION**: ${m}`);
  }

  // Oil and escalation summary
  const oilEmoji = turn.oil_price > 150 ? '🔴' : turn.oil_price > 120 ? '🟡' : '🟢';
  const escEmoji = turn.escalation_level > 8 ? '🔴' : turn.escalation_level > 5 ? '🟡' : '🟢';
  lines.push(`${oilEmoji} Oil: $${turn.oil_price.toFixed(0)}/bbl | ${escEmoji} Escalation: ${turn.escalation_level.toFixed(1)}/10 | Phase: ${turn.escalation_phase.replace(/_/g, ' ')}`);

  return lines;
}

export function NarrativeFeed({ turns }: { turns: TurnReport[] }) {
  if (turns.length === 0) {
    return (
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Narrative Feed</h3>
        <div className="text-xs text-text-muted italic">No events yet. Step the simulation to begin.</div>
      </div>
    );
  }

  return (
    <div className="bg-bg-card border border-border rounded-lg p-4">
      <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Narrative Feed</h3>
      <div className="space-y-4 max-h-96 overflow-auto pr-2">
        {[...turns].reverse().map((turn) => {
          const lines = narrateTurn(turn);
          return (
            <div key={turn.turn} className="border-l-2 border-border pl-3 space-y-1">
              {lines.map((line, i) => (
                <div
                  key={i}
                  className={`text-xs ${i === 0 ? 'text-text-primary font-semibold' : 'text-text-muted'}`}
                  dangerouslySetInnerHTML={{
                    __html: line
                      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-text-primary">$1</strong>')
                  }}
                />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
