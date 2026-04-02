interface NullStateProps {
  message?: string
  className?: string
}

export function NullState({ message = '—', className = '' }: NullStateProps) {
  return (
    <span className={`text-text-secondary text-sm italic ${className}`}>
      {message}
    </span>
  )
}
