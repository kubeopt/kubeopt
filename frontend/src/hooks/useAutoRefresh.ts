import { useCallback, useEffect, useRef, useState } from 'react'

interface UseAutoRefreshOptions {
  intervalMs?: number
  enabled?: boolean
}

export function useAutoRefresh(
  callback: () => Promise<void> | void,
  { intervalMs = 30_000, enabled = true }: UseAutoRefreshOptions = {},
) {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const callbackRef = useRef(callback)
  callbackRef.current = callback

  const refresh = useCallback(async () => {
    setIsRefreshing(true)
    try {
      await callbackRef.current()
      setLastRefresh(new Date())
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return
    const id = setInterval(refresh, intervalMs)
    return () => clearInterval(id)
  }, [enabled, intervalMs, refresh])

  return { isRefreshing, lastRefresh, refresh }
}
