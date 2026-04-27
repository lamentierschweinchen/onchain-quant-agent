interface AnalysisBlockProps {
  text: string
  label?: string
  className?: string
}

export function AnalysisBlock({
  text,
  label = 'Analysis',
  className = '',
}: AnalysisBlockProps) {
  return (
    <div
      className={`relative bg-surface border border-border rounded-md p-4 pl-5 ${className}`}
    >
      <span className="absolute left-0 top-3 bottom-3 w-[2px] bg-accent-cyan/40" />
      <div className="flex items-baseline justify-between mb-2">
        <span className="eyebrow text-accent-cyan/80">{label}</span>
        <span className="text-[10px] text-text-faint font-mono uppercase tracking-wider">
          Narrative
        </span>
      </div>
      <p className="text-[13px] text-text-secondary leading-relaxed">{text}</p>
    </div>
  )
}
