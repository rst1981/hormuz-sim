import { useEffect, useState } from 'react';
import { useUpdateStore } from '../stores/updateStore';
import type { SituationUpdate, ParameterChange } from '../types';

const STATUS_COLORS: Record<string, string> = {
  pending: '#d29922',
  applied: '#3fb950',
  rejected: '#f85149',
};

const DATA_SOURCES = [
  'iranmonitor.org',
  'News API',
  'X / Twitter',
  'Polymarket',
  'AirNav Radar',
  'MarineTraffic',
  'GeoConfirmed',
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
}: {
  update: SituationUpdate;
  onApprove: () => void;
  onReject: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-bg-card border border-border rounded-lg p-4 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-text-muted">{update.date}</span>
          <span className="text-xs text-text-muted">{update.source}</span>
          <StatusBadge status={update.status} />
        </div>
        {update.status === 'pending' && (
          <div className="flex gap-1.5">
            <button
              onClick={onApprove}
              className="px-2.5 py-1 text-xs rounded bg-bg-hover border border-border text-[#3fb950] hover:bg-[#3fb95015] transition-colors"
            >
              Approve
            </button>
            <button
              onClick={onReject}
              className="px-2.5 py-1 text-xs rounded bg-bg-hover border border-border text-[#f85149] hover:bg-[#f8514915] transition-colors"
            >
              Reject
            </button>
          </div>
        )}
      </div>

      <p className="text-sm text-text-primary">{update.summary}</p>

      {update.parameter_changes.length > 0 && (
        <div className="space-y-1 pt-1">
          {update.parameter_changes.map((c, i) => (
            <ChangeDisplay key={i} change={c} />
          ))}
        </div>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        className="text-[10px] text-text-accent hover:underline"
      >
        {expanded ? 'Hide source text' : 'Show source text'}
      </button>

      {expanded && (
        <pre className="text-[11px] text-text-muted bg-bg-primary border border-border rounded p-2 whitespace-pre-wrap max-h-40 overflow-y-auto">
          {update.raw_text}
        </pre>
      )}
    </div>
  );
}

function BaselinePanel({ baseline }: { baseline: Record<string, Record<string, number>> | null }) {
  if (!baseline) return null;

  return (
    <div className="bg-bg-card border border-border rounded-lg p-4 space-y-3">
      <h3 className="text-xs uppercase tracking-wider text-text-muted">Current Baseline</h3>
      {Object.entries(baseline).map(([category, params]) => (
        <div key={category}>
          <div className="text-[10px] uppercase tracking-wider text-text-accent mb-1">{category.replace(/_/g, ' ')}</div>
          <div className="space-y-0.5">
            {Object.entries(params).map(([name, value]) => (
              <div key={name} className="flex justify-between text-xs font-mono">
                <span className="text-text-muted">{name}</span>
                <span className="text-text-primary">{typeof value === 'number' && value % 1 !== 0 ? value.toFixed(3) : value}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export function SituationUpdatesPage() {
  const {
    updates, baseline, crawling, loading, error,
    fetchUpdates, fetchBaseline, triggerCrawl, approve, reject,
    saveSnapshot,
  } = useUpdateStore();
  const [filter, setFilter] = useState<string>('');
  const [snapshotName, setSnapshotName] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchUpdates();
    fetchBaseline();
  }, [fetchUpdates, fetchBaseline]);

  const filtered = filter ? updates.filter(u => u.status === filter) : updates;
  const sorted = [...filtered].reverse();

  const handleSaveSnapshot = async () => {
    if (!snapshotName.trim()) return;
    setSaving(true);
    await saveSnapshot(snapshotName.trim());
    setSnapshotName('');
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      {/* Hero: Scrape button + sources */}
      <div className="bg-bg-card border border-border rounded-lg p-8 text-center space-y-4">
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

      {/* Save Baseline Snapshot */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-2">Save Current Baseline</h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={snapshotName}
            onChange={e => setSnapshotName(e.target.value)}
            placeholder="Snapshot name (e.g. March 17 baseline)"
            className="flex-1 px-3 py-2 bg-bg-primary border border-border rounded text-sm text-text-primary placeholder:text-text-muted"
            onKeyDown={e => e.key === 'Enter' && handleSaveSnapshot()}
          />
          <button
            onClick={handleSaveSnapshot}
            disabled={!snapshotName.trim() || saving}
            className="px-4 py-2 bg-bg-hover border border-border rounded text-sm text-text-primary hover:text-text-accent transition-colors disabled:opacity-40"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-1">
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
        <span className="text-xs text-text-muted self-center ml-2">{sorted.length} updates</span>
      </div>

      {/* Updates + Baseline panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-3">
          {sorted.length === 0 && !loading && (
            <div className="text-sm text-text-muted text-center py-8">
              No updates yet. Click "Scrape OSINT / News" to fetch the latest intelligence.
            </div>
          )}
          {sorted.map(update => (
            <UpdateCard
              key={update.id}
              update={update}
              onApprove={() => approve(update.id)}
              onReject={() => reject(update.id)}
            />
          ))}
        </div>

        <div>
          <BaselinePanel baseline={baseline} />
        </div>
      </div>
    </div>
  );
}

export default SituationUpdatesPage;
