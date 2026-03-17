import { useSimulationStore } from '../../stores/simulationStore';

export function Header() {
  const { simId, simState, loading } = useSimulationStore();

  return (
    <header className="h-12 bg-bg-card border-b border-border flex items-center justify-between px-4">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${simId ? 'bg-ceasefire' : 'bg-text-muted'}`} />
          <span className="text-xs text-text-muted font-mono">
            {simId ? `SIM:${simId}` : 'No simulation'}
          </span>
        </div>
        {simState && (
          <>
            <span className="text-xs text-text-muted">|</span>
            <span className="text-xs font-mono text-text-primary">
              Turn {simState.turn} · Day {simState.day}
            </span>
            <span className="text-xs text-text-muted">|</span>
            <span className="text-xs font-mono text-text-muted">
              {new Date(simState.calendar_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
            <span className="text-xs text-text-muted">|</span>
            <span className="text-xs font-mono text-text-accent">
              Day {simState.day} of war
            </span>
          </>
        )}
      </div>
      <div className="flex items-center gap-4">
        {simState && (
          <>
            <Badge label="OIL" value={`$${simState.oil_market.price.toFixed(0)}`} color="#d29922" />
            <Badge label="ESC" value={simState.escalation.level.toFixed(1)} color="#f85149" />
            <Badge label={simState.termination.outcome.toUpperCase()} value="" color={simState.termination.outcome === 'continuing' ? '#8b949e' : '#3fb950'} />
          </>
        )}
        {loading && <span className="text-xs text-text-accent animate-pulse">Loading...</span>}
      </div>
    </header>
  );
}

function Badge({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[10px] uppercase tracking-wider text-text-muted">{label}</span>
      <span className="text-xs font-mono font-semibold" style={{ color }}>{value}</span>
    </div>
  );
}
