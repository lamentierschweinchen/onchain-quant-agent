import { useEffect, useState, useCallback } from 'react'

/**
 * Minimal pathname-based router. Avoids pulling in react-router for two routes.
 *
 * Reads window.location.pathname, listens for popstate, exposes a navigate()
 * that uses history.pushState and re-fires popstate so subscribers update.
 */
export function useRoute() {
  const [path, setPath] = useState<string>(() => window.location.pathname)

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  const navigate = useCallback((to: string) => {
    if (to === window.location.pathname) return
    window.history.pushState(null, '', to)
    window.dispatchEvent(new PopStateEvent('popstate'))
  }, [])

  return { path, navigate }
}

/** Anchor that uses pushState instead of full page nav. */
export function PageLink({
  to,
  className,
  children,
  onNavigate,
}: {
  to: string
  className?: string
  children: React.ReactNode
  onNavigate?: () => void
}) {
  return (
    <a
      href={to}
      className={className}
      onClick={(e) => {
        // Let cmd/ctrl-click open in a new tab — normal browser behavior.
        if (e.metaKey || e.ctrlKey || e.shiftKey) return
        e.preventDefault()
        if (to !== window.location.pathname) {
          window.history.pushState(null, '', to)
          window.dispatchEvent(new PopStateEvent('popstate'))
        }
        onNavigate?.()
      }}
    >
      {children}
    </a>
  )
}
