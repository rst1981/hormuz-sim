import { create } from 'zustand';
import type { SituationUpdate, BaselineState, BaselineSnapshot } from '../types';
import * as api from '../api/client';

interface UpdateStore {
  updates: SituationUpdate[];
  baseline: BaselineState | null;
  projectedBaseline: BaselineState | null;
  availableDates: string[];
  snapshots: BaselineSnapshot[];
  loading: boolean;
  crawling: boolean;
  error: string | null;

  fetchUpdates: (status?: string) => Promise<void>;
  fetchBaseline: (date?: string) => Promise<void>;
  fetchProjectedBaseline: () => Promise<void>;
  fetchDates: () => Promise<void>;
  fetchSnapshots: () => Promise<void>;
  saveSnapshot: (name: string) => Promise<void>;
  deleteSnapshot: (id: string) => Promise<void>;
  triggerCrawl: () => Promise<SituationUpdate[]>;
  approve: (id: string) => Promise<void>;
  reject: (id: string) => Promise<void>;
}

export const useUpdateStore = create<UpdateStore>((set, _get) => ({
  updates: [], baseline: null, projectedBaseline: null, availableDates: [], snapshots: [],
  loading: false, crawling: false, error: null,

  fetchUpdates: async (status) => {
    set({ loading: true, error: null });
    try {
      const updates = await api.getUpdates(status);
      set({ updates, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  fetchBaseline: async (date) => {
    try {
      const baseline = await api.getBaseline(date);
      set({ baseline });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  fetchProjectedBaseline: async () => {
    try {
      const projectedBaseline = await api.getProjectedBaseline();
      set({ projectedBaseline });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  fetchDates: async () => {
    try {
      const availableDates = await api.getAvailableDates();
      set({ availableDates });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  fetchSnapshots: async () => {
    try {
      const snapshots = await api.listSnapshots();
      set({ snapshots });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  saveSnapshot: async (name) => {
    try {
      await api.saveSnapshot(name);
      const snapshots = await api.listSnapshots();
      set({ snapshots });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  deleteSnapshot: async (id) => {
    try {
      await api.deleteSnapshot(id);
      const snapshots = await api.listSnapshots();
      set({ snapshots });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  triggerCrawl: async () => {
    set({ crawling: true, error: null });
    try {
      const result = await api.triggerCrawl();
      // Refresh the full list + projected baseline
      const updates = await api.getUpdates();
      const projectedBaseline = await api.getProjectedBaseline();
      set({ updates, projectedBaseline, crawling: false });
      return result.updates;
    } catch (e) {
      set({ error: (e as Error).message, crawling: false });
      return [];
    }
  },

  approve: async (id) => {
    try {
      await api.approveUpdate(id);
      const updates = await api.getUpdates();
      const baseline = await api.getBaseline();
      const projectedBaseline = await api.getProjectedBaseline();
      const availableDates = await api.getAvailableDates();
      set({ updates, baseline, projectedBaseline, availableDates });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  reject: async (id) => {
    try {
      await api.rejectUpdate(id);
      const updates = await api.getUpdates();
      const projectedBaseline = await api.getProjectedBaseline();
      set({ updates, projectedBaseline });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },
}));
