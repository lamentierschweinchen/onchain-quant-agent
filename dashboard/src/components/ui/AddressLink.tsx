import { useState } from 'react'
import { truncateAddress } from '../../lib/formatters'
import { accountUrl } from '../../lib/constants'

interface AddressLinkProps {
  address: string
  label?: string | null
}

export function AddressLink({ address, label }: AddressLinkProps) {
  const [copied, setCopied] = useState(false)

  function handleCopy(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    navigator.clipboard.writeText(address).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  const truncated = truncateAddress(address)
  const url = accountUrl(address)

  return (
    <span className="inline-flex items-center gap-1.5 group">
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex flex-col hover:text-accent-cyan transition-colors"
      >
        {label ? (
          <>
            <span className="text-text-primary text-sm font-medium">{label}</span>
            <span className="font-mono text-xs text-text-secondary">{truncated}</span>
          </>
        ) : (
          <span className="font-mono text-sm text-text-secondary hover:text-accent-cyan transition-colors">
            {truncated}
          </span>
        )}
      </a>
      <button
        onClick={handleCopy}
        title="Copy address"
        className="opacity-0 group-hover:opacity-100 transition-opacity text-text-secondary hover:text-accent-cyan p-0.5 rounded"
        aria-label="Copy full address"
      >
        {copied ? (
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="1.5 6 4.5 9 10.5 3" />
          </svg>
        ) : (
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="4" y="4" width="7" height="7" rx="1" />
            <path d="M8 4V2a1 1 0 0 0-1-1H2a1 1 0 0 0-1 1v5a1 1 0 0 0 1 1h2" />
          </svg>
        )}
      </button>
    </span>
  )
}
