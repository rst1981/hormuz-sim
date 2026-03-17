import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { colors } from '../theme';
import { createSim, stepSim, getSimState, destroySim, getSimTurns } from '../api/client';
import type { TurnReport } from '../types';
import { ResetButton } from '../components/ResetButton';

interface BranchRun {
  turns: TurnReport[];
  outcome: string;
  finalTurn: number;
}

export function BranchComparisonPage() {
  const [variant, setVariant] = useState('baseline');
  const [maxSteps, setMaxSteps] = useState(60);
  const [loading, setLoading] = useState(false);
  const [branchA, setBranchA] = useState<BranchRun | null>(null);
  const [branchB, setBranchB] = useState<BranchRun | null>(null);

  const runBranch = async (branch?: string): Promise<BranchRun> => {
    const { sim_id } = await createSim(variant, undefined, branch);
    let outcome = 'continuing';
    for (let i = 0; i < maxSteps; i++) {
      const report = await stepSim(sim_id);
      if (report.termination_status !== 'continuing') {
        outcome = report.termination_status;
        break;
      }
    }
    const state = await getSimState(sim_id);
    const turns = await getSimTurns(sim_id);
    if (outcome === 'continuing') outcome = state.termination.outcome;
    destroySim(sim_id).catch(() => {});
    return { turns, outcome, finalTurn: turns.length };
  };

  const handleLaunch = async () => {
    setLoading(true);
    setBranchA(null);
    setBranchB(null);
    try {
      const [a, b] = await Promise.all([
        runBranch(undefined),
        runBranch('b'),
      ]);
      setBranchA(a);
      setBranchB(b);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleReset = () => {
    setBranchA(null);
    setBranchB(null);
  };

  // Build comparison chart data
  const maxLen = Math.max(branchA?.turns.length ?? 0, branchB?.turns.length ?? 0);
  const oilData = Array.from({ length: maxLen }, (_, i) => ({
    turn: i + 1,
    'Branch A': branchA?.turns[i]?.oil_price ?? null,
    'Branch B': branchB?.turns[i]?.oil_price ?? null,
  }));
  const escData = Array.from({ length: maxLen }, (_, i) => ({
    turn: i + 1,
    'Branch A': branchA?.turns[i]?.escalation_level ?? null,
    'Branch B': branchB?.turns[i]?.escalation_level ?? null,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Ensemble Model Comparison</h2>
        {(branchA || branchB) && <ResetButton onClick={handleReset} label="Reset" />}
      </div>

      {/* Branch Theory Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <BranchCard
          title="Branch A: Wittman-Zartman"
          description="Agent belief convergence model. Wars end when opposing military actors agree on who's winning (Wittman) AND political actors perceive mutual ripeness (Zartman)."
          features={[
            'Bayesian belief updating with noisy signals',
            'P(victory) convergence tracking',
            'Zartman ripeness with rolling averages',
            'Faction-weighted termination desire',
            'Miscalculation-driven escalation spirals',
          ]}
          color={colors.chart.coalition}
          result={branchA}
        />
        <BranchCard
          title="Branch B: Fearon / DIA"
          description="Duration-based hazard model. War duration follows a hazard function estimated from DIA historical data, with Bayesian Model Averaging across crisis archetypes."
          features={[
            'Hazard rate duration estimation',
            'Survival function tracking',
            'BMA across 4 crisis archetypes',
            'Information-theoretic learning rate',
            'Commitment problem resolution dynamics',
          ]}
          color={colors.chart.iran}
          result={branchB}
        />
      </div>

      {/* Launch Controls */}
      <div className="bg-bg-card border border-border rounded-lg p-4 flex flex-wrap gap-4 items-end">
        <div>
          <label className="text-[10px] uppercase text-text-muted block mb-1">Variant</label>
          <select value={variant} onChange={e => setVariant(e.target.value)}
            className="bg-bg-input border border-border rounded px-3 py-1.5 text-sm text-text-primary">
            <option value="baseline">Baseline</option>
            <option value="houthi_activation">Houthi Activation</option>
            <option value="interceptor_crisis">Interceptor Crisis</option>
            <option value="mojtaba_surfaces">Mojtaba Surfaces</option>
            <option value="russian_confirmed">Russian Confirmed</option>
            <option value="uprising_breakthrough">Uprising Breakthrough</option>
            <option value="chinese_carrier">Chinese Carrier</option>
            <option value="strait_trap">Strait Trap</option>
          </select>
        </div>
        <div>
          <label className="text-[10px] uppercase text-text-muted block mb-1">Max Turns</label>
          <input type="number" value={maxSteps} onChange={e => setMaxSteps(+e.target.value)} min={10} max={120}
            className="bg-bg-input border border-border rounded px-3 py-1.5 text-sm font-mono w-24 text-text-primary" />
        </div>
        <button onClick={handleLaunch} disabled={loading}
          className="px-4 py-1.5 bg-text-accent text-bg-primary rounded text-sm font-medium hover:opacity-90 disabled:opacity-50">
          {loading ? 'Running both branches...' : 'Launch Comparison'}
        </button>
      </div>

      {/* Comparison Charts */}
      {branchA && branchB && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Oil Price — A vs B</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={oilData}>
                <XAxis dataKey="turn" tick={{ fontSize: 10, fill: '#8b949e' }} />
                <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="Branch A" stroke={colors.chart.coalition} strokeWidth={2} dot={false} connectNulls />
                <Line type="monotone" dataKey="Branch B" stroke={colors.chart.iran} strokeWidth={2} dot={false} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Escalation — A vs B</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={escData}>
                <XAxis dataKey="turn" tick={{ fontSize: 10, fill: '#8b949e' }} />
                <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} domain={[0, 10]} />
                <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="Branch A" stroke={colors.chart.coalition} strokeWidth={2} dot={false} connectNulls />
                <Line type="monotone" dataKey="Branch B" stroke={colors.chart.iran} strokeWidth={2} dot={false} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Outcome Comparison */}
          <div className="bg-bg-card border border-border rounded-lg p-4 col-span-full">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Outcome Comparison</h3>
            <div className="grid grid-cols-2 gap-6">
              <OutcomeCard label="Branch A: Wittman-Zartman" outcome={branchA.outcome} turns={branchA.finalTurn} color={colors.chart.coalition} />
              <OutcomeCard label="Branch B: Fearon / DIA" outcome={branchB.outcome} turns={branchB.finalTurn} color={colors.chart.iran} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function BranchCard({ title, description, features, color, result }: {
  title: string; description: string; features: string[]; color: string; result: BranchRun | null;
}) {
  return (
    <div className={`bg-bg-card border rounded-lg p-4 ${result ? 'border-text-accent' : 'border-border'}`}>
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 rounded-full" style={{ background: color }} />
        <h3 className="text-sm font-semibold">{title}</h3>
        {result && (
          <span className="text-[9px] bg-ceasefire/20 text-ceasefire px-1.5 py-0.5 rounded uppercase">
            {result.outcome.replace(/_/g, ' ')} — {result.finalTurn} turns
          </span>
        )}
      </div>
      <p className="text-xs text-text-muted mb-3">{description}</p>
      <ul className="space-y-1">
        {features.map((f, i) => (
          <li key={i} className="text-xs text-text-primary">• {f}</li>
        ))}
      </ul>
    </div>
  );
}

function OutcomeCard({ label, outcome, turns, color }: { label: string; outcome: string; turns: number; color: string }) {
  return (
    <div className="text-center">
      <div className="text-[10px] uppercase tracking-wider text-text-muted mb-2">{label}</div>
      <div className="text-2xl font-mono font-bold" style={{ color }}>
        {outcome.replace(/_/g, ' ').toUpperCase()}
      </div>
      <div className="text-xs text-text-muted mt-1">Terminated at turn {turns}</div>
    </div>
  );
}
