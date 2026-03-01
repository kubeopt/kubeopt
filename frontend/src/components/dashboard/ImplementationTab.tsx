import { useEffect, useState } from 'react'
import { Check, Copy, Download, ChevronDown, ChevronRight } from 'lucide-react'
import Markdown from 'react-markdown'
import { getPlan, generatePlan } from '../../api/plans'
import { getChartData } from '../../api/analysis'
import Card from '../common/Card'
import Button from '../common/Button'
import Badge from '../common/Badge'
import LoadingSpinner from '../common/LoadingSpinner'

interface ImplementationTabProps {
  clusterId: string
}

interface Command {
  command: string
  description: string
  priority_score: number
  risk_level: string
}

function CopyButton({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs transition-colors"
      style={{ color: 'var(--text-muted)' }}
      title="Copy to clipboard"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
      {label && <span>{copied ? 'Copied' : label}</span>}
    </button>
  )
}

export default function ImplementationTab({ clusterId }: ImplementationTabProps) {
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [expandedPhases, setExpandedPhases] = useState<Record<string, boolean>>({})

  const fetchPlan = async () => {
    setLoading(true)
    try {
      // Fetch AI plan and analysis data in parallel
      const [planResult, chartResult] = await Promise.allSettled([
        getPlan(clusterId),
        getChartData(clusterId),
      ])

      let mergedPlan: Record<string, unknown> = {}

      // Extract AI-generated plan
      if (planResult.status === 'fulfilled' && planResult.value) {
        const planData = planResult.value as Record<string, unknown>
        // Plan might be nested under 'plan' key
        const nested = planData.plan as Record<string, unknown> | undefined
        if (nested && typeof nested === 'object') {
          mergedPlan = { ...planData, ...nested }
        } else if (!planData.message?.toString().includes('No plan')) {
          mergedPlan = planData
        }
      }

      // Extract execution plan commands from analysis chart data
      if (chartResult.status === 'fulfilled' && chartResult.value) {
        const cd = chartResult.value as Record<string, unknown>
        const execPlan = cd.execution_plan as Record<string, Command[]> | undefined
        const cmdsByCat = cd.commands_by_category as Record<string, Command[]> | undefined
        if (execPlan && Object.keys(execPlan).length > 0) {
          mergedPlan.commands_by_category = execPlan
        } else if (cmdsByCat && Object.keys(cmdsByCat).length > 0) {
          mergedPlan.commands_by_category = cmdsByCat
        }
      }

      setPlan(Object.keys(mergedPlan).length > 0 ? mergedPlan : null)
    } catch {
      setPlan(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPlan() }, [clusterId])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await generatePlan(clusterId)
      await fetchPlan()
    } catch {
      // Error handled
    } finally {
      setGenerating(false)
    }
  }

  const togglePhase = (phase: string) => {
    setExpandedPhases((prev) => ({ ...prev, [phase]: !prev[phase] }))
  }

  if (loading) return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>

  // Extract markdown from various possible fields
  const markdownPlan = (
    (plan?.raw_markdown as string) ||
    (plan?.markdown_content as string) ||
    (plan?.markdown_plan as string) ||
    (plan?.plan_text as string) ||
    ''
  )

  const phases = (plan?.phases || plan?.commands_by_category || {}) as Record<string, Command[]>
  const totalSavings = typeof plan?.total_savings === 'number'
    ? plan.total_savings
    : typeof plan?.total_monthly_savings === 'number'
      ? plan.total_monthly_savings
      : 0

  // Collect all commands for "Copy All" / "Download"
  const allCommands = Object.entries(phases).flatMap(([phase, cmds]) =>
    (cmds as Command[]).map((c) => `# ${phase}: ${c.description}\n${c.command}`),
  )

  const downloadMarkdown = () => {
    const lines: string[] = [`# Implementation Plan — ${clusterId}\n`]
    if (totalSavings > 0) lines.push(`Estimated savings: $${(totalSavings as number).toFixed(0)}/month\n`)
    if (markdownPlan) lines.push(markdownPlan, '\n---\n')
    Object.entries(phases).forEach(([phase, cmds]) => {
      lines.push(`## ${phase.replace(/_/g, ' ')}\n`)
      ;(cmds as Command[]).forEach((c) => {
        lines.push(`### ${c.description} [${c.risk_level}]\n\`\`\`bash\n${c.command}\n\`\`\`\n`)
      })
    })
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `implementation-plan-${clusterId}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const hasPlan = Object.keys(phases).length > 0 || markdownPlan

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Implementation Plan</h3>
          {(totalSavings as number) > 0 && (
            <p className="text-sm text-green-600">
              Estimated savings: ${(totalSavings as number).toFixed(0)}/month
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {hasPlan && (
            <>
              <Button variant="secondary" size="sm" onClick={downloadMarkdown}>
                <Download className="mr-1.5 h-4 w-4" /> Download
              </Button>
              {allCommands.length > 0 && (
                <CopyButton text={allCommands.join('\n\n')} label="Copy All" />
              )}
            </>
          )}
          <Button onClick={handleGenerate} disabled={generating} size="sm">
            {generating ? 'Generating...' : 'Generate AI Plan'}
          </Button>
        </div>
      </div>

      {/* AI-generated markdown plan */}
      {markdownPlan && (
        <Card>
          <h4 className="mb-3 font-medium" style={{ color: 'var(--text-secondary)' }}>AI Plan</h4>
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <Markdown>{markdownPlan}</Markdown>
          </div>
        </Card>
      )}

      {!hasPlan ? (
        <Card className="py-8 text-center" style={{ color: 'var(--text-muted)' }}>
          No implementation plan available. Run an analysis first, then generate a plan.
        </Card>
      ) : (
        Object.entries(phases).map(([phaseName, commands]) => {
          const isExpanded = expandedPhases[phaseName] !== false // default open
          return (
            <Card key={phaseName}>
              <button
                onClick={() => togglePhase(phaseName)}
                className="flex w-full items-center gap-2 text-left"
              >
                {isExpanded ? <ChevronDown className="h-4 w-4" style={{ color: 'var(--text-muted)' }} /> : <ChevronRight className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />}
                <h4 className="font-medium capitalize" style={{ color: 'var(--text-secondary)' }}>
                  {phaseName.replace(/_/g, ' ')}
                </h4>
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>({(commands as Command[]).length} commands)</span>
              </button>
              {isExpanded && (
                <div className="mt-3 space-y-2">
                  {(commands as Command[]).map((cmd, i) => (
                    <div key={i} className="rounded-lg border p-3" style={{ borderColor: 'var(--border-subtle)' }}>
                      <div className="flex items-start justify-between">
                        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{cmd.description}</p>
                        <Badge variant={cmd.risk_level === 'low' ? 'green' : cmd.risk_level === 'high' ? 'red' : 'yellow'}>
                          {cmd.risk_level}
                        </Badge>
                      </div>
                      <div className="mt-2 flex items-start justify-between rounded px-2 py-1" style={{ backgroundColor: 'var(--bg-surface)' }}>
                        <code className="text-xs" style={{ color: 'var(--text-secondary)' }}>{cmd.command}</code>
                        <CopyButton text={cmd.command} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )
        })
      )}
    </div>
  )
}
