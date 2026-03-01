import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { clsx } from 'clsx'
import { Play } from 'lucide-react'
import Button from '../components/common/Button'
import OverviewTab from '../components/dashboard/OverviewTab'
import PodsTab from '../components/dashboard/PodsTab'
import WorkloadsTab from '../components/dashboard/WorkloadsTab'
import ResourcesTab from '../components/dashboard/ResourcesTab'
import ImplementationTab from '../components/dashboard/ImplementationTab'
import AlertsTab from '../components/dashboard/AlertsTab'
import AnalysisProgressBar from '../components/analysis/AnalysisProgressOverlay'
import { analyzeCluster, getClusterInfo } from '../api/clusters'
import { useAnalysis } from '../hooks/useAnalysis'

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'pods', label: 'Pods' },
  { id: 'workloads', label: 'Workloads' },
  { id: 'resources', label: 'Resources' },
  { id: 'implementation', label: 'Implementation' },
  { id: 'alerts', label: 'Alerts' },
] as const

type TabId = typeof tabs[number]['id']

export default function Dashboard() {
  const { id } = useParams<{ id: string }>()
  const clusterId = decodeURIComponent(id || '')
  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [clusterInfo, setClusterInfo] = useState<Record<string, unknown> | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const { progress, isRunning, startListening } = useAnalysis(clusterId)

  const subscriptionId = (clusterInfo?.subscription_id as string) || ''
  const clusterName = (clusterInfo?.cluster_name as string) || clusterId

  // Fetch cluster info on mount to get subscription_id etc.
  const fetchClusterInfo = useCallback(async () => {
    if (!clusterId) return
    try {
      const info = await getClusterInfo(clusterId)
      setClusterInfo(info)
    } catch {
      // Cluster info fetch failed — tabs will show empty state
    }
  }, [clusterId])

  useEffect(() => { fetchClusterInfo() }, [fetchClusterInfo])

  // Alt+1..6 keyboard shortcuts for tab navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!e.altKey) return
      const idx = parseInt(e.key, 10)
      if (idx >= 1 && idx <= tabs.length) {
        e.preventDefault()
        setActiveTab(tabs[idx - 1].id)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // When analysis completes, refresh the current tab data
  useEffect(() => {
    if (progress?.status === 'completed') {
      setRefreshKey((k) => k + 1)
      fetchClusterInfo()
    }
  }, [progress?.status, fetchClusterInfo])

  const handleAnalyze = async () => {
    try {
      await analyzeCluster(clusterId)
      startListening()
    } catch {
      // Analysis trigger failed
    }
  }

  const renderTab = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab key={refreshKey} clusterId={clusterId} />
      case 'pods':
        return <PodsTab key={refreshKey} clusterId={clusterId} subscriptionId={subscriptionId} />
      case 'workloads':
        return <WorkloadsTab key={refreshKey} clusterId={clusterId} subscriptionId={subscriptionId} />
      case 'resources':
        return <ResourcesTab key={refreshKey} clusterId={clusterId} subscriptionId={subscriptionId} />
      case 'implementation':
        return <ImplementationTab key={refreshKey} clusterId={clusterId} />
      case 'alerts':
        return <AlertsTab key={refreshKey} clusterId={clusterId} />
    }
  }

  return (
    <div>
      {/* MongoDB-style analysis progress bar at the very top */}
      <AnalysisProgressBar progress={progress} isRunning={isRunning} />

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{clusterName}</h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>
            {clusterId}
          </p>
        </div>
        <Button size="sm" onClick={handleAnalyze} disabled={isRunning}>
          <Play className="mr-1.5 h-4 w-4" />
          {isRunning ? 'Analyzing...' : 'Run Analysis'}
        </Button>
      </div>

      {/* Tab navigation */}
      <div className="mb-6" style={{ borderBottomWidth: 1, borderBottomStyle: 'solid', borderBottomColor: 'var(--border-subtle)' }}>
        <nav className="-mb-px flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'border-b-2 pb-3 text-sm font-medium transition-colors',
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent hover:text-primary-600 dark:hover:text-primary-400',
              )}
              style={activeTab !== tab.id ? { color: 'var(--text-muted)' } : undefined}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div key={`${activeTab}-${refreshKey}`} className="animate-fadeIn">
        {renderTab()}
      </div>
    </div>
  )
}
