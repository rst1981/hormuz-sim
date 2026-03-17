export interface TurnReport {
  turn: number;
  day: number;
  actions: { agent_id: string; action: ActionRecord }[];
  random_events: { name: string; description: string }[];
  oil_price: number;
  escalation_level: number;
  escalation_phase: string;
  termination_status: string;
  trump_mode: string;
  iran_dominant_faction: string;
  key_metrics: Record<string, number>;
  miscalculation_events: string[];
}

export interface ActionRecord {
  action_type: string;
  target: string | null;
  intensity: number;
  parameters: Record<string, unknown>;
  description: string;
  signal_cost: number;
}

export interface GroundTruth {
  mojtaba_alive: number; irgc_cohesion: number;
  iran_missile_stocks: number; iran_drone_stocks: number;
  israel_interceptor_stocks: number; us_pgm_stocks: number;
  iran_nuclear_progress: number; iran_cyber_capability: number;
  fordow_destroyed: number; kharg_terminal_damaged: number;
  russia_supplying_iran: number; china_willing_to_guarantee: number;
  us_political_will: number; israel_will_to_continue: number;
  houthi_activation_prob: number; hezbollah_full_war_prob: number;
  uprising_intensity: number; uprising_irgc_drain: number;
  irgc_casualties_cumulative: number; uprising_casualties_cumulative: number;
  regime_survival_index: number;
}

export interface Belief {
  type: 'beta' | 'gaussian';
  mean: number;
  std: number;
  alpha?: number; beta?: number; concentration?: number;
  precision?: number;
}

export interface FactionState {
  faction_id: string; name: string; influence: number;
  hardline_score: number; p_victory: number;
  beliefs: Record<string, Belief>;
  preferred_actions: string[];
}

export interface AgentState {
  agent_id: string; name: string; type: string;
  active: boolean; p_victory: number;
  beliefs: Record<string, Belief>;
  victory_weights: Record<string, { weight: number; target: number }>;
  // StochasticAgent
  current_mode?: string; turns_in_mode?: number;
  transition_matrix?: Record<string, Record<string, number>>;
  // CompositeAgent
  factions?: FactionState[]; dominant_faction?: string;
  resolution_mode?: string;
  mode_inertia?: number;
  max_mode_duration?: number;
  // MilitaryAgent
  accumulated_cost?: number;
  // PoliticalAgent
  current_pain?: number; ripeness?: number;
  // ProxyAgent
  patron_id?: string; autonomy?: number;
}

export interface StraitStatus {
  chinese_flow: number; indian_flow: number; russian_flow: number;
  western_flow: number; gulf_state_flow: number;
  trap_mode: boolean; overall_flow: number;
}

export interface OilMarketState {
  price: number; base_price: number; strait: StraitStatus;
  red_sea: { houthi_active: boolean; flow: number };
  kharg_damaged: number; war_risk_premium: number;
  spr_releases: number; russian_backfill: number;
  demand_destruction: number; ceasefire_probability: number;
  panic_level: number; price_history: number[];
  price_change_pct: number; trend: string;
}

export interface EscalationState {
  level: number; phase: string; trend: string;
  richardson_state: Record<string, { grievance: number; reactivity: number; fatigue: number }>;
  history: number[];
  miscalculation_events: string[];
}

export interface TerminationState {
  outcome: string; low_escalation_turns: number; max_turns: number;
  convergence_history: Record<string, number[]>;
  ripeness_history: Record<string, number[]>;
}

export interface SimState {
  turn: number; day: number; variant: string;
  calendar_date: string; start_day: number; start_date: string;
  ground_truth: GroundTruth;
  agents: Record<string, AgentState>;
  oil_market: OilMarketState;
  escalation: EscalationState;
  termination: TerminationState;
  insurance: Record<string, unknown>;
}

export interface RunResult {
  run_id: number; variant: string; outcome: string;
  turns: number; final_oil_price: number; final_escalation: number;
  final_metrics: Record<string, number>; seed: number;
}

export interface Stats { mean: number; min: number; max: number; std: number; median: number; }

export interface MCResult {
  variant: string; n_runs: number;
  outcome_distribution: Record<string, number>;
  duration_stats: Stats; oil_price_stats: Stats; escalation_stats: Stats;
  runs: RunResult[];
}

export interface MCStatus { status: string; completed: number; total: number; }

export interface ParamDef {
  name: string; type: string; default: number;
  min?: number; max?: number; description: string;
}

export interface Variant { id: string; name: string; description: string; }

// Situation Updates
export interface ParameterChange {
  parameter: string;
  category: string;
  delta: number | null;
  absolute: number | null;
  new_value: number | null;
  reasoning: string;
}

export interface SituationUpdate {
  id: string;
  date: string;
  source: string;
  source_url: string | null;
  raw_text: string;
  summary: string;
  category: string;
  parameter_changes: ParameterChange[];
  status: 'pending' | 'applied' | 'rejected';
  reviewed_at: string | null;
  created_at: string;
}

export interface BaselineState {
  ground_truth: Record<string, number>;
  oil_market: Record<string, number>;
  escalation: Record<string, number>;
}

export interface BaselineSnapshot {
  id: string;
  name: string;
  date: string;
  baseline: BaselineState;
  created_at: string;
}
