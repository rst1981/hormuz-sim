import { create } from 'zustand';
import type { MCResult, MCStatus, RunResult } from '../types';
import * as api from '../api/client';
import { simWS } from '../api/websocket';

interface MCJob {
  jobId: string;
  status: MCStatus;
  results: MCResult | null;
  runs: RunResult[];
}

interface MonteCarloStore {
  jobs: Record<string, MCJob>;
  activeJobId: string | null;
  launch: (variant: string, nRuns: number, maxTurns?: number, seed?: number) => Promise<void>;
  pollStatus: (jobId: string) => Promise<void>;
  loadResults: (jobId: string) => Promise<void>;
  addRunResult: (jobId: string, run: RunResult) => void;
  updateProgress: (jobId: string, completed: number, total: number) => void;
  setComplete: (jobId: string, results: MCResult) => void;
  reset: () => void;
}

export const useMonteCarloStore = create<MonteCarloStore>((set, get) => ({
  jobs: {}, activeJobId: null,

  launch: async (variant, nRuns, maxTurns = 120, seed) => {
    const { job_id } = await api.launchMC({ variant, n_runs: nRuns, max_turns: maxTurns, seed });
    const job: MCJob = {
      jobId: job_id,
      status: { status: 'running', completed: 0, total: nRuns },
      results: null, runs: [],
    };
    set(s => ({ jobs: { ...s.jobs, [job_id]: job }, activeJobId: job_id }));

    // Connect WebSocket for streaming
    simWS.connectMC(
      job_id,
      (run) => get().addRunResult(job_id, run),
      (completed, total) => get().updateProgress(job_id, completed, total),
      (results) => get().setComplete(job_id, results),
    );
  },

  pollStatus: async (jobId) => {
    const status = await api.getMCStatus(jobId);
    set(s => ({
      jobs: { ...s.jobs, [jobId]: { ...s.jobs[jobId], status } },
    }));
  },

  loadResults: async (jobId) => {
    const results = await api.getMCResults(jobId);
    set(s => ({
      jobs: { ...s.jobs, [jobId]: { ...s.jobs[jobId], results, status: { status: 'completed', completed: results.n_runs, total: results.n_runs } } },
    }));
  },

  addRunResult: (jobId, run) => set(s => {
    const job = s.jobs[jobId];
    if (!job) return s;
    return { jobs: { ...s.jobs, [jobId]: { ...job, runs: [...job.runs, run] } } };
  }),

  updateProgress: (jobId, completed, total) => set(s => {
    const job = s.jobs[jobId];
    if (!job) return s;
    return { jobs: { ...s.jobs, [jobId]: { ...job, status: { status: 'running', completed, total } } } };
  }),

  setComplete: (jobId, results) => set(s => {
    const job = s.jobs[jobId];
    if (!job) return s;
    return { jobs: { ...s.jobs, [jobId]: { ...job, results, status: { status: 'completed', completed: results.n_runs, total: results.n_runs } } } };
  }),

  reset: () => {
    simWS.disconnect();
    set({ jobs: {}, activeJobId: null });
  },
}));
