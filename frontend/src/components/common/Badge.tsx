import { clsx } from 'clsx'

interface BadgeProps {
  variant?: 'green' | 'yellow' | 'red' | 'blue' | 'gray'
  children: React.ReactNode
}

export default function Badge({ variant = 'gray', children }: BadgeProps) {
  return (
    <span
      className={clsx('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', {
        'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400': variant === 'green',
        'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400': variant === 'yellow',
        'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400': variant === 'red',
        'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400': variant === 'blue',
        'bg-gray-100 text-gray-800 dark:bg-dark-700 dark:text-dark-300': variant === 'gray',
      })}
    >
      {children}
    </span>
  )
}
