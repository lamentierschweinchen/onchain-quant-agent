import { Fragment, useMemo } from 'react'

/**
 * The meta-learning log is written for the next agent run, so it legitimately
 * names scripts, JSON fields and contract functions. Left as plain prose those
 * identifiers read as typos. Setting them in mono tells a human reader at a
 * glance which fragments are code and can be skipped.
 */
const IDENTIFIER =
  /\b(?:[a-z][a-z0-9]*(?:_[a-z0-9]+)+(?:\.py|\.json|\.ts|\.tsx)?|[a-z]+[A-Z][a-zA-Z]+|\/[a-z][a-zA-Z0-9_/{}]*)\b/g

export function CodeAwareText({
  text,
  className = '',
}: {
  text: string
  className?: string
}) {
  const parts = useMemo(() => {
    const out: Array<{ code: boolean; value: string }> = []
    let last = 0
    for (const m of text.matchAll(IDENTIFIER)) {
      const i = m.index ?? 0
      if (i > last) out.push({ code: false, value: text.slice(last, i) })
      out.push({ code: true, value: m[0] })
      last = i + m[0].length
    }
    if (last < text.length) out.push({ code: false, value: text.slice(last) })
    return out
  }, [text])

  return (
    <span className={className}>
      {parts.map((p, i) =>
        p.code ? (
          <code
            key={i}
            className="font-mono text-[0.92em] text-accent-cyan/85 bg-accent-cyan/[0.07] rounded px-[3px] py-[1px]"
          >
            {p.value}
          </code>
        ) : (
          <Fragment key={i}>{p.value}</Fragment>
        ),
      )}
    </span>
  )
}
