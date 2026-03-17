import { create } from 'zustand';
import type { ParamDef } from '../types';
import * as api from '../api/client';

interface ParameterStore {
  groundTruth: ParamDef[];
  oilMarket: ParamDef[];
  escalation: ParamDef[];
  overrides: Record<string, number>;
  loaded: boolean;
  loadDefaults: () => Promise<void>;
  setOverride: (name: string, value: number) => void;
  resetOverrides: () => void;
}

export const useParameterStore = create<ParameterStore>((set) => ({
  groundTruth: [], oilMarket: [], escalation: [], overrides: {}, loaded: false,

  loadDefaults: async () => {
    const [gt, oil, esc] = await Promise.all([
      api.getParamDefaults('ground-truth'),
      api.getParamDefaults('oil-market'),
      api.getParamDefaults('escalation'),
    ]);
    set({ groundTruth: gt, oilMarket: oil, escalation: esc, loaded: true });
  },

  setOverride: (name, value) => set(s => ({
    overrides: { ...s.overrides, [name]: value },
  })),

  resetOverrides: () => set({ overrides: {} }),
}));
