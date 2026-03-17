export function ResetButton({ onClick, label = 'Reset' }: { onClick: () => void; label?: string }) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1 text-xs font-mono text-text-muted border border-border rounded hover:text-escalation hover:border-escalation/50 transition-colors"
      title={label}
    >
      ↺ {label}
    </button>
  );
}
