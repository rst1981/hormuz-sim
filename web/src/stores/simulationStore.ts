import { create } from 'zustand';
import type { SimState, TurnReport } from '../types';
import * as api from '../api/client';

interface SimulationStore {
  simId: string | null;
  simState: SimState | null;
  turns: TurnReport[];
  loading: boolean;
  error: string | null;
  createSim: (variant?: string, overrides?: Record<string, unknown>, branch?: string, startDate?: string, snapshotId?: string) => Promise<void>;
  stepSim: () => Promise<TurnReport | null>;
  runSim: () => Promise<void>;
  loadState: () => Promise<void>;
  loadTurns: () => Promise<void>;
  reset: () => void;
}

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  simId: null, simState: null, turns: [], loading: false, error: null,

  createSim: async (variant = 'baseline', overrides, branch, startDate, snapshotId) => {
    set({ loading: true, error: null });
    try {
      const { sim_id } = await api.createSim(variant, overrides, branch, startDate, snapshotId);
      set({ simId: sim_id, turns: [], simState: null });
      const state = await api.getSimState(sim_id);
      set({ simState: state, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  stepSim: async () => {
    const { simId } = get();
    if (!simId) return null;
    set({ loading: true, error: null });
    try {
      const report = await api.stepSim(simId);
      const state = await api.getSimState(simId);
      set(s => ({ turns: [...s.turns, report], simState: state, loading: false }));
      return report;
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
      return null;
    }
  },

  runSim: async () => {
    const { simId } = get();
    if (!simId) return;
    set({ loading: true, error: null });
    try {
      const result = await api.runSim(simId);
      const turns = await api.getSimTurns(simId);
      set({ simState: result.final_state, turns, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  loadState: async () => {
    const { simId } = get();
    if (!simId) return;
    try {
      const state = await api.getSimState(simId);
      set({ simState: state });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  loadTurns: async () => {
    const { simId } = get();
    if (!simId) return;
    try {
      const turns = await api.getSimTurns(simId);
      set({ turns });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  reset: () => {
    const { simId } = get();
    if (simId) api.destroySim(simId).catch(() => {});
    set({ simId: null, simState: null, turns: [], loading: false, error: null });
  },
}));
