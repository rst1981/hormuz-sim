import { useSimulationStore } from '../stores/simulationStore';
import { TRUMP_COLORS } from '../theme';
import { ResetButton } from '../components/ResetButton';

const MODES = ['rally', 'deal', 'escalation', 'distraction'] as const;

export function TrumpTrackerPage() {
  const { simState, turns, reset } = useSimulationStore();
  const trump = simState?.agents?.us_trump;
  const matrix = trump?.transition_matrix;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Trump Tracker</h2>
        <ResetButton onClick={reset} label="New Sim" />
      </div>

      {/* Mode Timeline */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Mode Timeline</h3>
        <div className="flex h-8 rounded overflow-hidden">
          {turns.map((t, i) => (
            <div
              key={i}
              className="flex-1 relative group"
              style={{ background: TRUMP_COLORS[t.trump_mode] || '#8b949e' }}
              title={`Turn ${t.turn}: ${t.trump_mode}`}
            >
              {i > 0 && turns[i - 1].trump_mode !== t.trump_mode && (
                <div className="absolute left-0 top-0 h-full w-0.5 bg-bg-primary" />
              )}
            </div>
          ))}
        </div>
        <div className="flex gap-4 mt-2">
          {MODES.map(m => (
            <div key={m} className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded" style={{ background: TRUMP_COLORS[m] }} />
              <span className="text-[10px] text-text-muted capitalize">{m}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Current State */}
      {trump && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Current State</h3>
            <div className="text-3xl font-mono font-bold mb-2"
              style={{ color: TRUMP_COLORS[trump.current_mode as keyof typeof TRUMP_COLORS] || '#8b949e' }}>
              {trump.current_mode?.toUpperCase()}
            </div>
            <div className="text-xs text-text-muted space-y-1">
              <div>Turns in mode: <span className="font-mono">{trump.turns_in_mode}</span></div>
              <div>Mode inertia: <span className="font-mono">{trump.mode_inertia}</span></div>
              <div>P(Victory): <span className="font-mono">{(trump.p_victory * 100).toFixed(0)}%</span></div>
            </div>
          </div>

          {/* Transition Matrix Heatmap */}
          {matrix && (
            <div className="bg-bg-card border border-border rounded-lg p-4">
              <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Transition Matrix</h3>
              <div className="grid grid-cols-5 gap-0.5">
                <div />
                {MODES.map(m => (
                  <div key={m} className="text-[9px] text-text-muted text-center capitalize">{m.slice(0, 4)}</div>
                ))}
                {MODES.map(from => (
                  <>
                    <div key={`label-${from}`} className="text-[9px] text-text-muted capitalize flex items-center">{from.slice(0, 4)}</div>
                    {MODES.map(to => {
                      const val = matrix[from]?.[to] ?? 0;
                      const intensity = Math.min(1, val * 2);
                      return (
                        <div
                          key={`${from}-${to}`}
                          className="aspect-square flex items-center justify-center text-[9px] font-mono rounded"
                          style={{
                            background: `rgba(88, 166, 255, ${intensity * 0.5})`,
                            color: intensity > 0.3 ? '#c9d1d9' : '#8b949e',
                          }}
                        >
                          {(val * 100).toFixed(0)}
                        </div>
                      );
                    })}
                  </>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Mode Distribution */}
      {turns.length > 0 && (
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Mode Distribution</h3>
          <div className="flex gap-2">
            {MODES.map(m => {
              const count = turns.filter(t => t.trump_mode === m).length;
              const pct = turns.length > 0 ? (count / turns.length) * 100 : 0;
              return (
                <div key={m} className="flex-1">
                  <div className="h-24 relative rounded overflow-hidden bg-bg-primary">
                    <div
                      className="absolute bottom-0 left-0 right-0 rounded-t transition-all"
                      style={{ height: `${pct}%`, background: TRUMP_COLORS[m] }}
                    />
                  </div>
                  <div className="text-center mt-1">
                    <div className="text-[10px] text-text-muted capitalize">{m}</div>
                    <div className="text-xs font-mono">{pct.toFixed(0)}%</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
