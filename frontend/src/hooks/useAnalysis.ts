import { useState, useEffect, useCallback, useRef } from 'react'

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

    // EventSource can't set Authorization header — pass token via query param
    const token = localStorage.getItem('kubeopt_token') || ''
    const url = `/api/clusters/${encodeURIComponent(clusterId)}/analysis-progress-stream?token=${encodeURIComponent(token)}`
    const es = new EventSource(url)
    eventSourceRef.current = es
    setIsRunning(true)
    setProgress({ status: 'starting', progress: 0, current_phase: 'Initializing...' })

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

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close()
    }
  }, [])

  return { progress, isRunning, startListening, stopListening }
}
