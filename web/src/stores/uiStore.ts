import { create } from 'zustand';

type Page = 'dashboard' | 'parameters' | 'montecarlo' | 'escalation' | 'oil' | 'agents' | 'trump' | 'comparison' | 'branches';

interface UIStore {
  sidebarOpen: boolean;
  activePage: Page;
  selectedAgentId: string | null;
  toggleSidebar: () => void;
  navigateTo: (page: Page) => void;
  selectAgent: (agentId: string | null) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: true,
  activePage: 'dashboard',
  selectedAgentId: null,
  toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),
  navigateTo: (page) => set({ activePage: page }),
  selectAgent: (agentId) => set({ selectedAgentId: agentId }),
}));
