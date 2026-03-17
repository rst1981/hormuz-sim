import type { TurnReport, SimState, AgentState, EscalationState, OilMarketState, TerminationState, MCResult, MCStatus, ParamDef, Variant, SituationUpdate, BaselineState, BaselineSnapshot } from '../types';

const BASE = import.meta.env.VITE_API_URL || '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

// Simulation
export const createSim = (variant = 'baseline', overrides?: Record<string, unknown>, branch?: string, start_date?: string, snapshot_id?: string) =>
  request<{ sim_id: string }>('/sim/create', { method: 'POST', body: JSON.stringify({ variant, overrides, branch, start_date, snapshot_id }) });

export const stepSim = (simId: string) =>
  request<TurnReport>(`/sim/${simId}/step`, { method: 'POST' });

export const runSim = (simId: string) =>
  request<{ outcome: string; turns: number; day: number; final_state: SimState }>(`/sim/${simId}/run`, { method: 'POST' });

export const getSimState = (simId: string) =>
  request<SimState>(`/sim/${simId}/state`);

export const getSimTurns = (simId: string) =>
  request<TurnReport[]>(`/sim/${simId}/turns`);

export const getAgents = (simId: string) =>
  request<Record<string, AgentState>>(`/sim/${simId}/agents`);

export const getAgent = (simId: string, agentId: string) =>
  request<AgentState>(`/sim/${simId}/agents/${agentId}`);

export const getEscalation = (simId: string) =>
  request<EscalationState>(`/sim/${simId}/escalation`);

export const getOilMarket = (simId: string) =>
  request<OilMarketState>(`/sim/${simId}/oil`);

export const getTermination = (simId: string) =>
  request<TerminationState>(`/sim/${simId}/termination`);

export const destroySim = (simId: string) =>
  request<{ status: string }>(`/sim/${simId}`, { method: 'DELETE' });

// Parameters
export const getParamDefaults = (category: string) =>
  request<ParamDef[]>(`/params/${category}/defaults`);

export const getTrumpMatrix = () =>
  request<Record<string, Record<string, number>>>('/params/trump/transition-matrix');

// Scenarios
export const getVariants = () =>
  request<Variant[]>('/scenarios/variants');

// Monte Carlo
export const launchMC = (config: { variant: string; n_runs: number; max_turns?: number; seed?: number }) =>
  request<{ job_id: string }>('/mc/launch', { method: 'POST', body: JSON.stringify(config) });

export const getMCStatus = (jobId: string) =>
  request<MCStatus>(`/mc/${jobId}/status`);

export const getMCResults = (jobId: string) =>
  request<MCResult>(`/mc/${jobId}/results`);

export const cancelMC = (jobId: string) =>
  request<{ status: string }>(`/mc/${jobId}/cancel`, { method: 'POST' });

// Comparison
export const launchComparison = (config: { variants: string[]; n_runs: number; max_turns?: number }) =>
  request<{ job_id: string }>('/compare/launch', { method: 'POST', body: JSON.stringify(config) });

export const getComparisonResults = (jobId: string) =>
  request<{ status: string; variants: string[]; results: Record<string, MCResult> }>(`/compare/${jobId}/results`);

// Export
export const exportCSV = async (simId: string): Promise<Blob> => {
  const res = await fetch(`${BASE}/export/csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sim_id: simId }),
  });
  return res.blob();
};

// Situation Updates
export const getUpdates = (status?: string, date?: string) => {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (date) params.set('date', date);
  const qs = params.toString();
  return request<SituationUpdate[]>(`/updates${qs ? `?${qs}` : ''}`);
};

export const getUpdate = (id: string) =>
  request<SituationUpdate>(`/updates/${id}`);

export const triggerCrawl = () =>
  request<{ message: string; updates: SituationUpdate[] }>('/updates/crawl', { method: 'POST' });

export const createManualUpdate = (data: {
  date: string; summary: string; raw_text?: string;
  parameter_changes?: { parameter: string; category: string; delta?: number; absolute?: number; reasoning?: string }[];
}) =>
  request<SituationUpdate>('/updates/manual', { method: 'POST', body: JSON.stringify(data) });

export const approveUpdate = (id: string) =>
  request<SituationUpdate>(`/updates/${id}/approve`, { method: 'POST' });

export const rejectUpdate = (id: string) =>
  request<SituationUpdate>(`/updates/${id}/reject`, { method: 'POST' });

export const deleteUpdate = (id: string) =>
  request<{ deleted: boolean }>(`/updates/${id}`, { method: 'DELETE' });

export const getBaseline = (date?: string) =>
  request<BaselineState>(`/updates/baseline${date ? `?date=${date}` : ''}`);

export const getProjectedBaseline = () =>
  request<BaselineState>('/updates/baseline/projected');

export const getAvailableDates = () =>
  request<string[]>('/updates/dates');

// Snapshots
export const listSnapshots = () =>
  request<BaselineSnapshot[]>('/snapshots');

export const saveSnapshot = (name: string) =>
  request<BaselineSnapshot>('/snapshots', { method: 'POST', body: JSON.stringify({ name }) });

export const deleteSnapshot = (id: string) =>
  request<{ deleted: boolean }>(`/snapshots/${id}`, { method: 'DELETE' });
