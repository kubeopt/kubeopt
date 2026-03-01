import { clsx } from 'clsx'

interface SkeletonProps {
  className?: string
}

function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={clsx(
        'animate-pulse rounded bg-gray-200 dark:bg-dark-700',
        className,
      )}
    />
  )
}

export function OverviewSkeleton() {
  return (
    <div className="space-y-6">
      {/* Metric cards row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-gray-200 p-4 dark:border-dark-700">
            <Skeleton className="mb-2 h-2.5 w-16" />
            <Skeleton className="mb-1 h-7 w-20" />
            <Skeleton className="h-3 w-12" />
          </div>
        ))}
      </div>
      {/* Cost trend full-width */}
      <div className="rounded-xl border border-gray-200 p-6 dark:border-dark-700">
        <Skeleton className="mb-4 h-4 w-24" />
        <Skeleton className="h-56 w-full" />
      </div>
      {/* Two-column chart grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-gray-200 p-6 dark:border-dark-700">
            <Skeleton className="mb-4 h-4 w-28" />
            <Skeleton className="h-48 w-full" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-6">
      <Skeleton className="h-8 w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-6 w-full" />
      ))}
    </div>
  )
}

export default Skeleton
