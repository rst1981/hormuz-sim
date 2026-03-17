import { useSimulationStore } from '../stores/simulationStore';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, BarChart, Bar } from 'recharts';
import { colors } from '../theme';
import { ResetButton } from '../components/ResetButton';

export function OilMarketPage() {
  const { simState, turns, reset } = useSimulationStore();
  const oil = simState?.oil_market;

  const priceData = turns.map(t => ({ turn: t.turn, price: t.oil_price }));

  const straitData = oil ? [
    { name: 'Chinese', flow: oil.strait.chinese_flow },
    { name: 'Indian', flow: oil.strait.indian_flow },
    { name: 'Russian', flow: oil.strait.russian_flow },
    { name: 'Western', flow: oil.strait.western_flow },
    { name: 'Gulf', flow: oil.strait.gulf_state_flow },
  ] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Oil Market</h2>
        <ResetButton onClick={reset} label="New Sim" />
      </div>

      {/* KPIs */}
      {oil && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <Metric label="Price" value={`$${oil.price.toFixed(0)}`} color={colors.chart.oil} />
          <Metric label="Change" value={`${oil.price_change_pct > 0 ? '+' : ''}${oil.price_change_pct.toFixed(0)}%`} color={oil.price_change_pct > 0 ? colors.chart.escalation : colors.outcomes.ceasefire} />
          <Metric label="Trend" value={oil.trend} color={colors.text.muted} />
          <Metric label="Panic" value={`${(oil.panic_level * 100).toFixed(0)}%`} color={colors.chart.escalation} />
          <Metric label="Strait Flow" value={`${(oil.strait.overall_flow * 100).toFixed(0)}%`} color={colors.chart.coalition} />
          <Metric label="War Premium" value={`$${oil.war_risk_premium.toFixed(0)}`} color={colors.chart.iran} />
        </div>
      )}

      {/* Price Chart */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Price Trajectory</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={priceData}>
            <XAxis dataKey="turn" tick={{ fontSize: 10, fill: '#8b949e' }} />
            <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} domain={['auto', 'auto']} />
            <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
            <Area type="monotone" dataKey="price" stroke={colors.chart.oil} fill={`${colors.chart.oil}30`} strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Strait Flow */}
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Strait of Hormuz Flow by Flag</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={straitData} layout="vertical">
              <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 10, fill: '#8b949e' }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fill: '#8b949e' }} width={60} />
              <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
              <Bar dataKey="flow" fill={colors.chart.coalition} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
          {oil?.strait.trap_mode && (
            <div className="text-xs text-escalation mt-2 font-semibold">⚠ STRAIT IN TRAP MODE — Combat Zone</div>
          )}
        </div>

        {/* Supply Breakdown */}
        {oil && (
          <div className="bg-bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Supply Disruption Offsets</h3>
            <div className="space-y-3">
              <BarRow label="SPR Releases" value={oil.spr_releases} max={0.15} />
              <BarRow label="Russian Backfill" value={oil.russian_backfill} max={0.1} />
              <BarRow label="Demand Destruction" value={oil.demand_destruction} max={0.1} />
              <BarRow label="Kharg Damage" value={oil.kharg_damaged} max={1} />
              <BarRow label="Ceasefire Prob" value={oil.ceasefire_probability} max={1} />
            </div>
            <div className="mt-4 text-xs text-text-muted">
              Red Sea: {oil.red_sea.houthi_active ? '⚠ Houthis Active' : 'Normal'} · Flow: {(oil.red_sea.flow * 100).toFixed(0)}%
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-bg-card border border-border rounded-lg p-3">
      <div className="text-[10px] uppercase tracking-wider text-text-muted">{label}</div>
      <div className="text-lg font-mono font-semibold mt-1" style={{ color }}>{value}</div>
    </div>
  );
}

function BarRow({ label, value, max }: { label: string; value: number; max: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-text-muted w-32">{label}</span>
      <div className="flex-1 h-2 bg-bg-primary rounded-full overflow-hidden">
        <div className="h-full bg-text-accent rounded-full" style={{ width: `${(value / max) * 100}%` }} />
      </div>
      <span className="text-xs font-mono w-12 text-right">{value.toFixed(3)}</span>
    </div>
  );
}
