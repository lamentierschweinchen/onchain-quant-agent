import { useLayoutEffect, useRef, useState } from 'react'

interface Props {
  text: string
  /** Lines shown before the reader has to ask for more. */
  lines?: number
  className?: string
  /** Label for the control; the default suits a paragraph of analysis. */
  moreLabel?: string
  lessLabel?: string
}

/**
 * Clamps a long passage to a few lines and reveals the rest on request.
 *
 * The report is deliberately verbose — it is a research log — but a reader
 * scanning the page should be able to see every finding without wading through
 * every justification. The toggle only renders when the text actually overflows,
 * so short passages stay clean.
 */
export function ExpandableText({
  text,
  lines = 2,
  className = '',
  moreLabel = 'More',
  lessLabel = 'Less',
}: Props) {
  const [expanded, setExpanded] = useState(false)
  const [overflows, setOverflows] = useState(false)
  const ref = useRef<HTMLParagraphElement>(null)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const check = () =>
      setOverflows(el.scrollHeight - el.clientHeight > 2)
    check()
    const ro = new ResizeObserver(check)
    ro.observe(el)
    return () => ro.disconnect()
  }, [text, lines])

  return (
    <div className={className}>
      <p
        ref={ref}
        style={
          expanded
            ? undefined
            : {
                display: '-webkit-box',
                WebkitLineClamp: lines,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }
        }
      >
        {text}
      </p>
      {(overflows || expanded) && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          className="mt-1 rounded px-2 py-1.5 -ml-2 text-[10.5px] font-mono uppercase tracking-wider text-accent-cyan/80 transition-colors duration-100 hover:bg-accent-cyan/10 hover:text-accent-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60"
        >
          {expanded ? lessLabel : moreLabel}
        </button>
      )}
    </div>
  )
}
