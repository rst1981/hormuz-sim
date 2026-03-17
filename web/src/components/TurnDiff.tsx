import type { SimState } from '../types';

interface DiffEntry {
  label: string;
  prev: number;
  curr: number;
  format: (n: number) => string;
  threshold: number;
}

function getDiffs(prev: SimState, curr: SimState): DiffEntry[] {
  const diffs: DiffEntry[] = [];
  const gt = curr.ground_truth;
  const pgt = prev.ground_truth;

  const entries: [string, keyof typeof gt, (n: number) => string, number][] = [
    ['Oil Price', 'regime_survival_index', (n) => `$${(n * 1).toFixed(0)}`, 0],
    ['Iran Missiles', 'iran_missile_stocks', (n) => `${(n * 100).toFixed(0)}%`, 0.01],
    ['Iran Drones', 'iran_drone_stocks', (n) => `${(n * 100).toFixed(0)}%`, 0.01],
    ['Israel Interceptors', 'israel_interceptor_stocks', (n) => `${(n * 100).toFixed(0)}%`, 0.01],
    ['US PGMs', 'us_pgm_stocks', (n) => `${(n * 100).toFixed(0)}%`, 0.01],
    ['Nuclear Progress', 'iran_nuclear_progress', (n) => `${(n * 100).toFixed(0)}%`, 0.005],
    ['IRGC Cohesion', 'irgc_cohesion', (n) => n.toFixed(2), 0.01],
    ['Regime Survival', 'regime_survival_index', (n) => `${(n * 100).toFixed(0)}%`, 0.01],
    ['Uprising Intensity', 'uprising_intensity', (n) => n.toFixed(2), 0.01],
    ['US Political Will', 'us_political_will', (n) => n.toFixed(2), 0.01],
    ['Israel Will', 'israel_will_to_continue', (n) => n.toFixed(2), 0.01],
  ];

  // Add oil price diff
  diffs.push({
    label: 'Oil Price',
    prev: prev.oil_market.price,
    curr: curr.oil_market.price,
    format: (n) => `$${n.toFixed(0)}`,
    threshold: 0.5,
  });

  // Add escalation diff
  diffs.push({
    label: 'Escalation',
    prev: prev.escalation.level,
    curr: curr.escalation.level,
    format: (n) => n.toFixed(2),
    threshold: 0.05,
  });

  // Ground truth diffs
  for (const [label, key, format, threshold] of entries) {
    if (label === 'Oil Price') continue; // already added
    const p = pgt[key] as number;
    const c = gt[key] as number;
    if (Math.abs(c - p) > threshold) {
      diffs.push({ label, prev: p, curr: c, format, threshold });
    }
  }

  return diffs.filter(d => Math.abs(d.curr - d.prev) > d.threshold);
}

export function TurnDiff({ prevState, currState }: { prevState: SimState | null; currState: SimState | null }) {
  if (!prevState || !currState) {
    return null;
  }

  const diffs = getDiffs(prevState, currState);

  if (diffs.length === 0) {
    return (
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">What Changed</h3>
        <div className="text-xs text-text-muted italic">No significant changes this turn.</div>
      </div>
    );
  }

  return (
    <div className="bg-bg-card border border-border rounded-lg p-4">
      <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">
        What Changed — Turn {prevState.turn} → {currState.turn}
      </h3>
      <div className="space-y-1.5">
        {diffs.map((d) => {
          const delta = d.curr - d.prev;
          const isUp = delta > 0;
          const color = isUp ? 'text-escalation' : 'text-ceasefire';
          const arrow = isUp ? '▲' : '▼';
          return (
            <div key={d.label} className="flex items-center justify-between text-xs">
              <span className="text-text-muted">{d.label}</span>
              <div className="flex items-center gap-2 font-mono">
                <span className="text-text-muted">{d.format(d.prev)}</span>
                <span className="text-text-muted">→</span>
                <span className="text-text-primary">{d.format(d.curr)}</span>
                <span className={`${color} min-w-[3rem] text-right`}>
                  {arrow} {Math.abs(delta).toFixed(delta > 10 ? 0 : 2)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
