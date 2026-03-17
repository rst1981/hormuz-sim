export const colors = {
  bg: { primary: '#0a0e14', card: '#111820', hover: '#1a2332', input: '#0d1117' },
  border: '#21262d',
  text: { primary: '#c9d1d9', muted: '#8b949e', accent: '#58a6ff' },
  chart: { iran: '#f0883e', coalition: '#58a6ff', oil: '#d29922', escalation: '#f85149' },
  trump: { rally: '#f0883e', deal: '#3fb950', escalation: '#f85149', distraction: '#8b949e' },
  factions: { hardliners: '#da3633', pragmatists: '#d29922', civilian: '#3fb950', succession: '#bc8cff' },
  outcomes: { ceasefire: '#3fb950', regime_collapse: '#f85149', interceptor_failure: '#d29922', frozen_conflict: '#8b949e', escalation_beyond_model: '#f85149', time_limit: '#58a6ff', continuing: '#8b949e' },
} as const;

export const OUTCOME_COLORS: Record<string, string> = colors.outcomes;
export const TRUMP_COLORS: Record<string, string> = colors.trump;
export const FACTION_COLORS: Record<string, string> = colors.factions;
