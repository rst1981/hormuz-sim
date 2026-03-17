import { useState, useEffect, useRef, useCallback } from 'react';
import { useSimulationStore } from '../stores/simulationStore';

const SPEEDS = [
  { label: '0.5x', ms: 2000 },
  { label: '1x', ms: 1000 },
  { label: '2x', ms: 500 },
  { label: '5x', ms: 200 },
];

export function ReplayControls() {
  const { simId, simState, stepSim, loading } = useSimulationStore();
  const [playing, setPlaying] = useState(false);
  const [speedIdx, setSpeedIdx] = useState(1);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const terminated = simState?.termination.outcome !== 'continuing';

  const stopPlayback = useCallback(() => {
    setPlaying(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (playing && !terminated && !loading) {
      timerRef.current = setInterval(() => {
        stepSim();
      }, SPEEDS[speedIdx].ms);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [playing, speedIdx, terminated, loading, stepSim]);

  useEffect(() => {
    if (terminated) stopPlayback();
  }, [terminated, stopPlayback]);

  if (!simId) return null;

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => stepSim()}
        disabled={loading || terminated}
        className="px-3 py-1.5 bg-bg-card border border-border rounded text-sm hover:bg-bg-hover transition-colors disabled:opacity-40 font-mono"
        title="Step one turn"
      >
        ⏭ Step
      </button>

      <button
        onClick={() => playing ? stopPlayback() : setPlaying(true)}
        disabled={terminated}
        className={`px-3 py-1.5 border rounded text-sm transition-colors font-mono ${
          playing
            ? 'bg-escalation/20 border-escalation text-escalation hover:bg-escalation/30'
            : 'bg-bg-card border-border hover:bg-bg-hover'
        } disabled:opacity-40`}
      >
        {playing ? '⏸ Pause' : '▶ Play'}
      </button>

      <div className="flex items-center gap-1 ml-1">
        {SPEEDS.map((s, i) => (
          <button
            key={s.label}
            onClick={() => setSpeedIdx(i)}
            className={`px-2 py-1 text-[10px] font-mono rounded transition-colors ${
              i === speedIdx
                ? 'bg-text-accent/20 text-text-accent border border-text-accent/50'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {simState && (
        <span className="text-xs text-text-muted font-mono ml-2">
          {simState.variant} · Turn {simState.turn} · Day {simState.day}
          {terminated && (
            <span className="ml-2 text-escalation">
              [{simState.termination.outcome.replace(/_/g, ' ')}]
            </span>
          )}
        </span>
      )}
    </div>
  );
}
