import { PageLink } from '../hooks/useRoute'

interface PageTabsProps {
  active: 'home' | 'code' | 'pump'
}

const TABS: Array<{ id: 'home' | 'code' | 'pump'; to: string; label: string }> = [
  { id: 'home', to: '/', label: 'Onchain' },
  { id: 'pump', to: '/pump', label: 'Pump' },
  { id: 'code', to: '/code', label: 'Code' },
]

export function PageTabs({ active }: PageTabsProps) {
  return (
    <div className="flex items-center gap-0.5">
      {TABS.map((tab) => {
        const isActive = tab.id === active
        return (
          <PageLink
            key={tab.id}
            to={tab.to}
            className={[
              'px-2.5 py-1 text-[10.5px] font-mono uppercase tracking-[0.12em] rounded transition-colors',
              isActive
                ? 'bg-accent-cyan/10 text-accent-cyan'
                : 'text-text-muted hover:text-text-primary hover:bg-surface',
            ].join(' ')}
          >
            {tab.label}
          </PageLink>
        )
      })}
    </div>
  )
}
