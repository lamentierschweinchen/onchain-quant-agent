import { useEffect, useRef, useState } from 'react'

/**
 * Pixel width of an element, kept current with a ResizeObserver.
 *
 * The older charts draw in a fixed viewBox and let the SVG scale, which shrinks
 * 9px axis labels to 5px on a phone. Charts that use this hook lay out in real
 * pixels instead, so type stays the size it was designed at on every screen.
 *
 * Width is null until the first measurement, so a chart can hold its height
 * without drawing at a guessed width and snapping.
 */
export function useElementWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  // Static renders (no layout, no effects) can inject a width for snapshots.
  const [width, setWidth] = useState<number | null>(
    () => (globalThis as { __STATIC_CHART_WIDTH__?: number }).__STATIC_CHART_WIDTH__ ?? null,
  )
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const update = () => setWidth(Math.max(260, Math.round(el.getBoundingClientRect().width)))
    update()
    const ro = new ResizeObserver(update)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return { ref, width }
}
