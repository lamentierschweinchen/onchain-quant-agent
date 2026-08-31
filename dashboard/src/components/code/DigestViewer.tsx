import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface DigestViewerProps {
  content: string | null
  loading: boolean
  date: string
}

export function DigestViewer({ content, loading, date }: DigestViewerProps) {
  if (loading && !content) {
    return (
      <article className="card p-12 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-6 h-6 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-text-muted text-[11px] font-mono uppercase tracking-wider">
            Loading {date}…
          </p>
        </div>
      </article>
    )
  }

  if (!content) {
    return (
      <article className="card p-12 flex items-center justify-center min-h-[400px]">
        <p className="text-text-muted text-[12px]">No content for this digest.</p>
      </article>
    )
  }

  return (
    <article className="card p-8 md:p-10">
      <div className="prose-mvx">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Open external links in a new tab for safety + UX
            a: ({ href, children, ...rest }) => (
              <a
                href={href}
                target={href?.startsWith('http') ? '_blank' : undefined}
                rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
                {...rest}
              >
                {children}
              </a>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </article>
  )
}
