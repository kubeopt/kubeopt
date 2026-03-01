export default function Footer() {
  return (
    <footer className="px-6 py-3" style={{ backgroundColor: 'var(--bg-sidebar)' }}>
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
        <div className="flex items-center gap-1.5">
          <img src="/kubeopt_eyecon.png" alt="" className="h-4 w-4" />
          <span>&copy; {new Date().getFullYear()} Nivaya Technologies</span>
        </div>
        <span>Built for Kubernetes &middot; Intelligent. Insightful. Illuminating.</span>
      </div>
    </footer>
  )
}
