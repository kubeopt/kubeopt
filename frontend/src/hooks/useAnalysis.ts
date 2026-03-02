import { useState, useEffect, useCallback, useRef } from 'react'
import { getAnalysisStatus } from '../api/clusters'

export interface AnalysisProgress {
  status: string
  progress: number
  current_phase?: string
  message?: string
}

export function useAnalysis(clusterId: string | null) {
  const [progress, setProgress] = useState<AnalysisProgress | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  const startListening = useCallback(() => {
    if (!clusterId) return

    // Close existing connection if any
    eventSourceRef.current?.close()

    // EventSource can't set Authorization header — pass token via query param
    const token = localStorage.getItem('kubeopt_token') || ''
    const url = `/api/clusters/${encodeURIComponent(clusterId)}/analysis-progress-stream?token=${encodeURIComponent(token)}`
    const es = new EventSource(url)
    eventSourceRef.current = es
    setIsRunning(true)

    es.onmessage = (event) => {
      try {
        const data: AnalysisProgress = JSON.parse(event.data)
        setProgress(data)
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'error') {
          setIsRunning(false)
          es.close()
        }
      } catch {
        // Ignore parse errors
      }
    }

    es.onerror = () => {
      setIsRunning(false)
      es.close()
    }
  }, [clusterId])

  const stopListening = useCallback(() => {
    eventSourceRef.current?.close()
    setIsRunning(false)
    setProgress(null)
  }, [])

  // On mount (or clusterId change), check if analysis is already running and auto-reconnect
  useEffect(() => {
    if (!clusterId) return

    let cancelled = false

    async function checkStatus() {
      try {
        const status = await getAnalysisStatus(clusterId!)
        if (cancelled) return
        if (status.status === 'analyzing' || status.status === 'starting') {
          // Analysis is in progress — reconnect to the SSE stream
          setProgress({
            status: status.status,
            progress: status.progress ?? 0,
            current_phase: status.current_phase,
            message: status.message,
          })
          startListening()
        }
      } catch {
        // Status check failed — not critical
      }
    }

    checkStatus()

    return () => {
      cancelled = true
      eventSourceRef.current?.close()
    }
  }, [clusterId, startListening])

  return { progress, isRunning, startListening, stopListening }
}
