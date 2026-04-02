import { useEffect, useRef, useState } from 'react'
import { SECTION_IDS, SECTION_LABELS } from '../lib/constants'

export function SectionNav() {
  const [activeId, setActiveId] = useState<string>(SECTION_IDS[0])
  const [tooltip, setTooltip] = useState<string | null>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)

  useEffect(() => {
    // Track which sections are currently visible and pick the topmost one.
    const visibleSections = new Set<string>()

    observerRef.current = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            visibleSections.add(entry.target.id)
          } else {
            visibleSections.delete(entry.target.id)
          }
        }

        // Pick the first section (in DOM order) that is currently visible.
        const ordered = SECTION_IDS.filter((id) => visibleSections.has(id))
        if (ordered.length > 0) {
          setActiveId(ordered[0])
        }
      },
      { threshold: 0.2, rootMargin: '-10% 0px -60% 0px' },
    )

    const observer = observerRef.current
    for (const id of SECTION_IDS) {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    }

    return () => observer.disconnect()
  }, [])

  function scrollTo(id: string) {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
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
            {/* Tooltip */}
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
