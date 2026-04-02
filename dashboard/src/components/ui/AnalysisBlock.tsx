interface AnalysisBlockProps {
  text: string
  className?: string
}

export function AnalysisBlock({ text, className = '' }: AnalysisBlockProps) {
  return (
    <blockquote
      className={`border-l-[3px] border-accent-cyan bg-surface rounded-r-lg p-4 ${className}`}
    >
      <p className="text-text-secondary leading-relaxed text-sm">{text}</p>
    </blockquote>
  )
}
