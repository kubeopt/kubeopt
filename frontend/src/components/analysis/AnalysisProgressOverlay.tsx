import type { AnalysisProgress } from '../../hooks/useAnalysis'

interface AnalysisProgressBarProps {
  progress: AnalysisProgress | null
  isRunning: boolean
}

/**
 * MongoDB Atlas-style analysis progress bar.
 * Sits at the very top of the cluster page as a thin, non-blocking banner.
 * When indeterminate (0%), shows a shimmer animation. Otherwise shows real %.
 */
export default function AnalysisProgressBar({ progress, isRunning }: AnalysisProgressBarProps) {
  if (!isRunning && !progress) return null

  const status = progress?.status || 'starting'
  const pct = progress?.progress || 0
  const phase = progress?.current_phase || progress?.message || 'Initializing...'
  const message = progress?.current_phase ? (progress?.message || '') : ''

  const done = status === 'completed'
  const failed = status === 'failed' || status === 'error'

  if (done) return null

  const barColor = failed
    ? 'bg-red-500'
    : 'bg-primary-500'

  return (
    <div className="mb-4 overflow-hidden rounded-lg border border-primary-200 bg-primary-50 dark:border-primary-800 dark:bg-primary-950/30">
      {/* Thin progress bar at top — shimmer when indeterminate */}
      <div className="h-1.5 w-full bg-gray-200 dark:bg-dark-700">
        {pct > 0 ? (
          <div
            className={`h-full ${barColor} transition-all duration-700 ease-out`}
            style={{ width: `${pct}%` }}
          />
        ) : (
          <div className="h-full w-full animate-pulse bg-gradient-to-r from-primary-300 via-primary-500 to-primary-300 bg-[length:200%_100%] animate-[shimmer_2s_ease-in-out_infinite]" />
        )}
      </div>

      {/* Info row */}
      <div className="flex items-center justify-between px-4 py-2">
        <div className="flex items-center gap-3">
          {!failed && (
            <div className="h-2 w-2 animate-pulse rounded-full bg-primary-500" />
          )}
          <span className="text-sm font-medium text-primary-800 dark:text-primary-300">
            {failed ? 'Analysis failed' : 'Analyzing cluster'}
          </span>
          <span className="text-sm text-primary-600 dark:text-primary-400">
            {phase}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {message && (
            <span className="max-w-xs truncate text-xs text-primary-500 dark:text-primary-400">
              {message}
            </span>
          )}
          {pct > 0 && (
            <span className="text-sm font-semibold text-primary-700 dark:text-primary-300">
              {pct.toFixed(0)}%
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
