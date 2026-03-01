import { clsx } from 'clsx'
import type { HTMLAttributes } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: boolean
}

export default function Card({ padding = true, className, children, style, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-xl shadow-sm',
        padding && 'p-6',
        className,
      )}
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderWidth: 1,
        borderStyle: 'solid',
        borderColor: 'var(--border-subtle)',
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  )
}
