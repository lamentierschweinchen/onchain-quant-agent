import { useMemo, useState } from 'react'

interface AnalysisBlockProps {
  text: string
  label?: string
  className?: string
  /** Paragraphs shown before the reader has to ask for more. */
  previewParagraphs?: number
}

/**
 * The agent writes these narratives as blank-line separated paragraphs. Rendering
 * them in a single <p> collapsed every break into a space and produced 4,000-character
 * walls of text — the main reason the page read as sprawl. We keep the paragraph
 * structure, and show only the opening beats until the reader asks for the rest.
 */
export function AnalysisBlock({
  text,
  label = 'Analysis',
  className = '',
  previewParagraphs = 2,
}: AnalysisBlockProps) {
  const [expanded, setExpanded] = useState(false)

  const paragraphs = useMemo(
    () =>
      (text ?? '')
        .split(/\n{2,}/)
        .map((p) => p.trim())
        .filter(Boolean),
    [text],
  )

  if (paragraphs.length === 0) return null

  const hasMore = paragraphs.length > previewParagraphs
  const visible = expanded ? paragraphs : paragraphs.slice(0, previewParagraphs)
  const hiddenCount = paragraphs.length - previewParagraphs

  return (
    <div
      className={`relative bg-surface border border-border rounded-md p-4 pl-5 ${className}`}
    >
      <span className="absolute left-0 top-3 bottom-3 w-[2px] bg-accent-cyan/40" />
      <div className="flex items-baseline justify-between mb-2 gap-3">
        <span className="eyebrow text-accent-cyan/80">{label}</span>
        <span className="text-[10px] text-text-faint font-mono uppercase tracking-wider shrink-0">
          {paragraphs.length === 1 ? 'Narrative' : `${paragraphs.length} points`}
        </span>
      </div>

      <div className="space-y-3">
        {visible.map((p, i) => (
          <p key={i} className="text-[13px] text-text-secondary leading-relaxed">
            {p}
          </p>
        ))}
      </div>

      {hasMore && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          className="mt-3 inline-flex items-center gap-1.5 rounded px-2 py-1 -ml-2 text-[11px] font-mono uppercase tracking-wider text-accent-cyan/90 transition-colors duration-100 hover:bg-accent-cyan/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60"
        >
          {expanded ? 'Show less' : `Read the full analysis · ${hiddenCount} more`}
          <span aria-hidden="true">{expanded ? '↑' : '↓'}</span>
        </button>
      )}
    </div>
  )
}
