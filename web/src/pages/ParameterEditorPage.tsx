import { useEffect } from 'react';
import { useParameterStore } from '../stores/parameterStore';
import { useSimulationStore } from '../stores/simulationStore';
import { ResetButton } from '../components/ResetButton';

export function ParameterEditorPage() {
  const { groundTruth, oilMarket, escalation, overrides, loaded, loadDefaults, setOverride, resetOverrides } = useParameterStore();
  const { createSim, loading } = useSimulationStore();

  useEffect(() => { if (!loaded) loadDefaults(); }, [loaded, loadDefaults]);

  const handleCreate = () => {
    const o = Object.keys(overrides).length > 0 ? overrides : undefined;
    createSim('baseline', o);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Parameter Editor</h2>
        <div className="flex gap-2">
          <ResetButton onClick={resetOverrides} label="Reset Params" />
          <button onClick={handleCreate} disabled={loading}
            className="px-4 py-1.5 text-xs bg-text-accent text-bg-primary rounded font-medium hover:opacity-90 disabled:opacity-50">
            {loading ? 'Creating...' : 'Create Simulation'}
          </button>
        </div>
      </div>

      {Object.keys(overrides).length > 0 && (
        <div className="text-xs text-text-accent bg-bg-card border border-text-accent/20 rounded p-2">
          {Object.keys(overrides).length} parameter(s) overridden
        </div>
      )}

      <ParamSection title="Ground Truth — Day 18 Starting Conditions" params={groundTruth} overrides={overrides} onSet={setOverride} />
      <ParamSection title="Oil Market" params={oilMarket} overrides={overrides} onSet={setOverride} />
      <ParamSection title="Escalation Dynamics" params={escalation} overrides={overrides} onSet={setOverride} />
    </div>
  );
}

function ParamSection({ title, params, overrides, onSet }: {
  title: string; params: { name: string; default: number; min?: number; max?: number; description: string }[];
  overrides: Record<string, number>; onSet: (name: string, value: number) => void;
}) {
  return (
    <div className="bg-bg-card border border-border rounded-lg p-4">
      <h3 className="text-xs uppercase tracking-wider text-text-muted mb-4">{title}</h3>
      <div className="space-y-3">
        {params.map(p => {
          const val = overrides[p.name] ?? p.default;
          const isOverridden = p.name in overrides;
          return (
            <div key={p.name} className="grid grid-cols-[200px_1fr_80px] gap-3 items-center">
              <div>
                <div className={`text-xs font-mono ${isOverridden ? 'text-text-accent' : 'text-text-primary'}`}>{p.name}</div>
                <div className="text-[10px] text-text-muted">{p.description}</div>
              </div>
              <input
                type="range"
                min={p.min ?? 0} max={p.max ?? 1} step={p.max && p.max > 10 ? 1 : 0.01}
                value={val}
                onChange={e => onSet(p.name, Number(e.target.value))}
                className="w-full accent-text-accent"
              />
              <span className="text-xs font-mono text-right">{typeof val === 'number' && val % 1 === 0 ? val : val.toFixed(2)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
