import { create } from 'zustand'

export interface Cluster {
  cluster_id: string
  cluster_name: string
  cloud_provider: string
  region?: string
  subscription_id?: string
  resource_group?: string
  last_analysis?: string
  optimization_score?: number
  total_cost?: number
  potential_savings?: number
  node_count?: number
  status: string
}

export interface PortfolioSummary {
  total_clusters: number
  total_monthly_cost: number
  total_potential_savings: number
  total_nodes: number
  average_optimization_score: number
  clusters_needing_attention: number
}

interface ClusterState {
  clusters: Cluster[]
  currentCluster: Cluster | null
  portfolioSummary: PortfolioSummary
  loading: boolean
  setClusters: (clusters: Cluster[]) => void
  setCurrentCluster: (cluster: Cluster | null) => void
  setPortfolioSummary: (summary: PortfolioSummary) => void
  setLoading: (loading: boolean) => void
}

export const useClusterStore = create<ClusterState>((set) => ({
  clusters: [],
  currentCluster: null,
  portfolioSummary: {
    total_clusters: 0,
    total_monthly_cost: 0,
    total_potential_savings: 0,
    total_nodes: 0,
    average_optimization_score: 0,
    clusters_needing_attention: 0,
  },
  loading: false,
  setClusters: (clusters) => set({ clusters }),
  setCurrentCluster: (cluster) => set({ currentCluster: cluster }),
  setPortfolioSummary: (summary) => set({ portfolioSummary: summary }),
  setLoading: (loading) => set({ loading }),
}))
