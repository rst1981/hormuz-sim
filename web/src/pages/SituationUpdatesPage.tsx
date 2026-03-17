import { useEffect, useState } from 'react';
import { useUpdateStore } from '../stores/updateStore';
import type { SituationUpdate, ParameterChange, BaselineState } from '../types';

const STATUS_COLORS: Record<string, string> = {
  pending: '#d29922',
  applied: '#3fb950',
  rejected: '#f85149',
};

const CATEGORY_META: Record<string, { label: string; color: string; icon: string }> = {
  conflict:   { label: 'Conflict & Military',  color: '#f85149', icon: '⚔' },
  maritime:   { label: 'Maritime & Strait',     color: '#58a6ff', icon: '⚓' },
  economy:    { label: 'Oil & Economy',         color: '#d29922', icon: '🛢' },
  sanctions:  { label: 'Sanctions',             color: '#bc8cff', icon: '🚫' },
  diplomacy:  { label: 'Diplomacy',             color: '#3fb950', icon: '🤝' },
  nuclear:    { label: 'Nuclear',               color: '#f0883e', icon: '☢' },
  politics:   { label: 'US/Intl Politics',      color: '#8b949e', icon: '🏛' },
  protest:    { label: 'Protest & Unrest',       color: '#da3633', icon: '✊' },
  general:    { label: 'General',               color: '#8b949e', icon: '📰' },
};

const CATEGORY_ORDER = ['conflict', 'maritime', 'economy', 'sanctions', 'nuclear', 'diplomacy', 'politics', 'protest', 'general'];

const DATA_SOURCES = [
  'Google News RSS',
  'iranmonitor.org',
  'X / Twitter',
  'Polymarket',
  'AirNav Radar',
  'MarineTraffic',
];

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className="text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded"
      style={{ color: STATUS_COLORS[status] ?? '#8b949e', borderColor: STATUS_COLORS[status] ?? '#8b949e', borderWidth: 1 }}
    >
      {status}
    </span>
  );
}

function ChangeDisplay({ change }: { change: ParameterChange }) {
  const value = change.absolute != null
    ? `= ${change.absolute}`
    : change.delta != null
      ? `${change.delta >= 0 ? '+' : ''}${change.delta.toFixed(3)}`
      : '?';

  return (
    <div className="flex items-center gap-2 text-xs font-mono">
      <span className="text-text-muted">{change.category}.</span>
      <span className="text-text-primary">{change.parameter}</span>
      <span style={{ color: change.delta != null && change.delta < 0 ? '#f85149' : '#3fb950' }}>{value}</span>
      <span className="text-text-muted truncate max-w-48">{change.reasoning}</span>
    </div>
  );
}

function UpdateCard({
  update,
  onApprove,
  onReject,
  onTestImpact,
  isTested,
}: {
  update: SituationUpdate;
  onApprove: () => void;
  onReject: () => void;
  onTestImpact: () => void;
  isTested: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`bg-bg-card border rounded-lg p-3 space-y-1.5 ${isTested ? 'border-[#58a6ff]' : 'border-border'}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-[10px] font-mono text-text-muted shrink-0">{update.date}</span>
          <StatusBadge status={update.status} />
          {update.source_url && (
            <a href={update.source_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-text-accent hover:underline shrink-0">↗</a>
          )}
        </div>
        {update.status === 'pending' && (
          <div className="flex gap-1 shrink-0">
            <button
              onClick={onTestImpact}
              className={`px-2 py-0.5 text-[10px] rounded border transition-colors ${
                isTested
                  ? 'bg-[#58a6ff15] border-[#58a6ff] text-[#58a6ff]'
                  : 'bg-bg-hover border-border text-text-muted hover:text-[#58a6ff]'
              }`}
            >
              {isTested ? 'Testing' : 'Test'}
            </button>
            <button
              onClick={onApprove}
              className="px-2 py-0.5 text-[10px] rounded bg-bg-hover border border-border text-[#3fb950] hover:bg-[#3fb95015] transition-colors"
            >
              Approve
            </button>
            <button
              onClick={onReject}
              className="px-2 py-0.5 text-[10px] rounded bg-bg-hover border border-border text-[#f85149] hover:bg-[#f8514915] transition-colors"
            >
              Reject
            </button>
          </div>
        )}
      </div>

      <p className="text-xs text-text-primary leading-snug">{update.summary}</p>

      {update.parameter_changes.length > 0 && (
        <div className="space-y-0.5">
          {update.parameter_changes.map((c, i) => (
            <ChangeDisplay key={i} change={c} />
          ))}
        </div>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        className="text-[10px] text-text-accent hover:underline"
      >
        {expanded ? 'Hide source' : 'Source'}
      </button>

      {expanded && (
        <pre className="text-[10px] text-text-muted bg-bg-primary border border-border rounded p-1.5 whitespace-pre-wrap max-h-24 overflow-y-auto">
          {update.raw_text}
        </pre>
      )}
    </div>
  );
}

function formatVal(value: number): string {
  return value % 1 !== 0 ? value.toFixed(3) : String(value);
}

function DualBaselinePanel({
  baseline,
  dynamic,
  dynamicLabel,
}: {
  baseline: BaselineState | null;
  dynamic: BaselineState | null;
  dynamicLabel: string;
}) {
  if (!baseline) return null;

  return (
    <div className="grid grid-cols-2 gap-3">
      {/* Current baseline — left half */}
      <div className="bg-bg-card border border-border rounded-lg p-3 space-y-2">
        <h3 className="text-[10px] uppercase tracking-wider text-text-muted font-semibold">Current Baseline</h3>
        {(Object.entries(baseline) as unknown as [string, Record<string, number>][]).map(([category, params]) => (
          <div key={category}>
            <div className="text-[10px] uppercase tracking-wider text-text-accent mb-0.5">{category.replace(/_/g, ' ')}</div>
            <div className="space-y-0">
              {Object.entries(params).map(([name, value]) => (
                <div key={name} className="flex justify-between text-[11px] font-mono leading-tight">
                  <span className="text-text-muted">{name}</span>
                  <span className="text-text-primary">{formatVal(value)}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Dynamic baseline — right half */}
      <div className={`bg-bg-card border rounded-lg p-3 space-y-2 ${dynamic ? 'border-[#58a6ff]' : 'border-border'}`}>
        <h3 className="text-[10px] uppercase tracking-wider font-semibold" style={{ color: dynamic ? '#58a6ff' : '#8b949e' }}>
          {dynamicLabel}
        </h3>
        {(Object.entries(baseline) as unknown as [string, Record<string, number>][]).map(([category, params]) => {
          const dynParams = dynamic
            ? (dynamic as unknown as Record<string, Record<string, number>>)[category]
            : null;

          return (
            <div key={category}>
              <div className="text-[10px] uppercase tracking-wider text-text-accent mb-0.5">{category.replace(/_/g, ' ')}</div>
              <div className="space-y-0">
                {Object.entries(params).map(([name, value]) => {
                  const dynVal = dynParams?.[name];
                  const changed = dynVal != null && Math.abs(dynVal - value) > 0.0001;
                  const delta = changed ? dynVal - value : 0;

                  return (
                    <div key={name} className={`flex justify-between text-[11px] font-mono leading-tight ${changed ? 'bg-[#58a6ff08] -mx-1 px-1 rounded' : ''}`}>
                      <span className="text-text-muted">{name}</span>
                      {changed ? (
                        <span className="flex items-center gap-1">
                          <span className="text-[#58a6ff] font-semibold">{formatVal(dynVal)}</span>
                          <span className={`text-[9px] ${delta > 0 ? 'text-[#3fb950]' : 'text-[#f85149]'}`}>
                            ({delta > 0 ? '+' : ''}{delta.toFixed(3)})
                          </span>
                        </span>
                      ) : (
                        <span className="text-text-muted">{dynamic ? formatVal(value) : '—'}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
        {!dynamic && (
          <p className="text-[10px] text-text-muted italic text-center py-4">
            Click "Test" on pending stories to preview their impact on the baseline
          </p>
        )}
      </div>
    </div>
  );
}

export function SituationUpdatesPage() {
  const {
    updates, baseline, testImpactBaseline, testedIds, crawling, loading, error,
    fetchUpdates, fetchBaseline, fetchProjectedBaseline, triggerCrawl,
    approve, reject, toggleTestImpact, testImpactMany, approveMany, rejectMany, clearTestImpact,
    saveSnapshot, fetchSnapshots,
  } = useUpdateStore();
  const [filter, setFilter] = useState<string>('');
  const [snapshotName, setSnapshotName] = useState('');
  const [saving, setSaving] = useState(false);
  const [expandedCats, setExpandedCats] = useState<Set<string>>(new Set());

  const toggleCat = (cat: string) => {
    setExpandedCats(prev => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat); else next.add(cat);
      return next;
    });
  };

  useEffect(() => {
    fetchUpdates();
    fetchBaseline();
    fetchProjectedBaseline();
    fetchSnapshots();
  }, [fetchUpdates, fetchBaseline, fetchProjectedBaseline, fetchSnapshots]);

  const filtered = filter ? updates.filter(u => u.status === filter) : updates;
  const sorted = [...filtered].reverse();

  // Group by category
  const grouped = CATEGORY_ORDER
    .map(cat => ({
      cat,
      meta: CATEGORY_META[cat] || CATEGORY_META.general,
      items: sorted.filter(u => (u.category || 'general') === cat),
    }))
    .filter(g => g.items.length > 0);

  const handleSaveSnapshot = async () => {
    if (!snapshotName.trim()) return;
    setSaving(true);
    await saveSnapshot(snapshotName.trim());
    setSnapshotName('');
    setSaving(false);
  };

  const testedCount = testedIds.size;

  return (
    <div className="space-y-4">
      {/* Hero: Scrape button + sources */}
      <div className="bg-bg-card border border-border rounded-lg p-6 text-center space-y-3">
        <h2 className="text-lg font-semibold text-text-primary">Situation Updates</h2>
        <button
          onClick={() => triggerCrawl()}
          disabled={crawling}
          className="px-8 py-3 bg-text-accent text-bg-primary rounded-lg text-base font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {crawling ? 'Scraping...' : 'Scrape OSINT / News'}
        </button>
        <div className="text-xs text-text-muted space-y-1">
          <p>Sources: {DATA_SOURCES.join(' \u00b7 ')}</p>
          <p>
            <a
              href="https://www.iranmonitor.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-accent hover:underline"
            >
              iranmonitor.org &#8599;
            </a>
          </p>
        </div>
      </div>

      {error && (
        <div className="text-xs text-[#f85149] bg-[#f8514910] border border-[#f8514930] rounded p-2">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-1">
        {['', 'pending', 'applied', 'rejected'].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              filter === s
                ? 'bg-bg-hover text-text-accent border border-text-accent'
                : 'bg-bg-card border border-border text-text-muted hover:text-text-primary'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
        <span className="text-xs text-text-muted ml-2">{sorted.length} updates</span>
        {testedCount > 0 && (
          <button
            onClick={clearTestImpact}
            className="ml-auto text-[10px] px-2 py-0.5 rounded border border-[#58a6ff] text-[#58a6ff] hover:bg-[#58a6ff15] transition-colors"
          >
            Clear {testedCount} tested
          </button>
        )}
      </div>

      {/* Story columns */}
      {sorted.length === 0 && !loading && (
        <div className="text-sm text-text-muted text-center py-8">
          No updates yet. Click "Scrape OSINT / News" to fetch the latest intelligence.
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {grouped.map(({ cat, meta, items }) => {
          const pendingItems = items.filter(u => u.status === 'pending');
          const pendingIds = pendingItems.map(u => u.id);
          const allTested = pendingItems.length > 0 && pendingItems.every(u => testedIds.has(u.id));

          return (
            <div key={cat} className="bg-bg-card border border-border rounded-lg overflow-hidden">
              {/* Header row: icon + label + count + expand toggle */}
              <button
                onClick={() => toggleCat(cat)}
                className="w-full flex items-center gap-2 px-3 py-2 hover:bg-bg-hover transition-colors"
              >
                <span style={{ color: meta.color }}>{meta.icon}</span>
                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: meta.color }}>
                  {meta.label}
                </span>
                <span className="text-[10px] text-text-muted">({items.length})</span>
                <span className="ml-auto text-[10px] text-text-muted">
                  {expandedCats.has(cat) ? '▼' : '▶'}
                </span>
              </button>

              {/* Bulk actions for pending items in this group */}
              {expandedCats.has(cat) && pendingItems.length > 0 && (
                <div className="flex items-center gap-1 px-3 pb-1.5 border-b border-border">
                  <span className="text-[10px] text-text-muted mr-auto">{pendingItems.length} pending</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); testImpactMany(pendingIds); }}
                    className={`px-2 py-0.5 text-[10px] rounded border transition-colors ${
                      allTested
                        ? 'bg-[#58a6ff15] border-[#58a6ff] text-[#58a6ff]'
                        : 'bg-bg-hover border-border text-text-muted hover:text-[#58a6ff]'
                    }`}
                  >
                    Test All
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); approveMany(pendingIds); }}
                    className="px-2 py-0.5 text-[10px] rounded bg-bg-hover border border-border text-[#3fb950] hover:bg-[#3fb95015] transition-colors"
                  >
                    Approve All
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); rejectMany(pendingIds); }}
                    className="px-2 py-0.5 text-[10px] rounded bg-bg-hover border border-border text-[#f85149] hover:bg-[#f8514915] transition-colors"
                  >
                    Reject All
                  </button>
                </div>
              )}

              {expandedCats.has(cat) && (
                <div className="px-2 pb-2 space-y-2 max-h-[28rem] overflow-y-auto">
                  {items.map(update => (
                    <UpdateCard
                      key={update.id}
                      update={update}
                      onApprove={() => approve(update.id)}
                      onReject={() => reject(update.id)}
                      onTestImpact={() => toggleTestImpact(update.id)}
                      isTested={testedIds.has(update.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Dual Baseline: Current vs Dynamic */}
      <DualBaselinePanel
        baseline={baseline}
        dynamic={testImpactBaseline}
        dynamicLabel={testedCount > 0 ? `Test Impact (${testedCount} stories)` : 'Test Impact'}
      />

      {/* Save Baseline Snapshot */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-2">Save Current Baseline as Snapshot</h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={snapshotName}
            onChange={e => setSnapshotName(e.target.value)}
            placeholder="Snapshot name (e.g. Post-scrape March 17)"
            className="flex-1 px-3 py-2 bg-bg-primary border border-border rounded text-sm text-text-primary placeholder:text-text-muted"
            onKeyDown={e => e.key === 'Enter' && handleSaveSnapshot()}
          />
          <button
            onClick={handleSaveSnapshot}
            disabled={!snapshotName.trim() || saving}
            className="px-4 py-2 bg-bg-hover border border-border rounded text-sm text-text-primary hover:text-text-accent transition-colors disabled:opacity-40"
          >
            {saving ? 'Saving...' : 'Save Snapshot'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SituationUpdatesPage;
