import { useEffect, useRef, useState } from 'react'
import { SECTION_IDS, SECTION_LABELS } from '../lib/constants'

/**
 * Scroll-spy nav. Replaces the prior IntersectionObserver implementation,
 * which broke for sections taller than the active band — a tall section
 * could be the only one inside the band, then exit before the next entered,
 * leaving the spy stuck on whichever section last fired.
 *
 * The fix: on every scroll, find the section whose top has just passed the
 * reference line (a fixed offset below the viewport top). That always
 * resolves to a single section regardless of section height.
 */
export function SectionNav() {
  const [activeId, setActiveId] = useState<string>(SECTION_IDS[0] as string)
  const [tooltip, setTooltip] = useState<string | null>(null)
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    function compute() {
      // Reference line: 30% down from the top of the viewport.
      // The section whose top has crossed this line most recently is "active".
      const referenceY = window.innerHeight * 0.3

      let bestId: string = SECTION_IDS[0]
      let bestTop = -Infinity

      for (const id of SECTION_IDS) {
        const el = document.getElementById(id)
        if (!el) continue
        const top = el.getBoundingClientRect().top
        // We want the largest top value that is still <= referenceY
        // (i.e. the section that has just passed the line, going down)
        if (top <= referenceY && top > bestTop) {
          bestTop = top
          bestId = id
        }
      }

      // If we're at the very top and nothing has crossed yet, default to first
      if (bestTop === -Infinity) {
        bestId = SECTION_IDS[0]
      }

      // If we're at the bottom of the page, force the last section
      // (handles the case where the last section is short and never
      // crosses the reference line)
      const atBottom =
        window.innerHeight + window.scrollY >=
        document.documentElement.scrollHeight - 16
      if (atBottom) {
        bestId = SECTION_IDS[SECTION_IDS.length - 1]
      }

      setActiveId((prev) => (prev === bestId ? prev : bestId))
    }

    function onScroll() {
      if (rafRef.current != null) return
      rafRef.current = requestAnimationFrame(() => {
        compute()
        rafRef.current = null
      })
    }

    // Initial compute + listener wiring
    compute()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)

    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  function scrollTo(id: string) {
    const el = document.getElementById(id)
    if (!el) return
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <nav
      className="fixed right-4 top-1/2 -translate-y-1/2 z-40 flex flex-col gap-2.5"
      aria-label="Section navigation"
    >
      {SECTION_IDS.map((id) => {
        const isActive = activeId === id
        const label = SECTION_LABELS[id] ?? id

        return (
          <div key={id} className="relative flex items-center justify-end">
            {tooltip === id && (
              <div className="absolute right-5 bg-surface border border-border text-text-primary text-xs px-2 py-1 rounded whitespace-nowrap pointer-events-none">
                {label}
              </div>
            )}
            <button
              onClick={() => scrollTo(id)}
              onMouseEnter={() => setTooltip(id)}
              onMouseLeave={() => setTooltip(null)}
              aria-label={`Go to ${label}`}
              aria-current={isActive ? 'true' : undefined}
              className={[
                'w-2.5 h-2.5 rounded-full transition-all duration-200 block',
                isActive
                  ? 'bg-accent-cyan scale-125 shadow-[0_0_6px_rgba(35,247,221,0.6)]'
                  : 'bg-border hover:bg-text-secondary',
              ].join(' ')}
            />
          </div>
        )
      })}
    </nav>
  )
}
