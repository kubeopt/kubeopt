import { useEffect, useState } from 'react'
import { Check, Copy, Download } from 'lucide-react'
import Markdown from 'react-markdown'
import { getPlan, generatePlan } from '../../api/plans'
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
      className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs text-dark-400 hover:bg-gray-100 dark:hover:bg-dark-700"
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

  const fetchPlan = async () => {
    setLoading(true)
    try {
      const data = await getPlan(clusterId) as Record<string, unknown>
      setPlan(data)
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

  if (loading) return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>

  const phases = (plan?.phases || plan?.commands_by_category || {}) as Record<string, Command[]>
  const markdownPlan = (plan?.markdown_plan || plan?.plan_text || '') as string
  const totalSavings = typeof plan?.total_savings === 'number' ? plan.total_savings : 0

  // Collect all commands for "Copy All" / "Download"
  const allCommands = Object.entries(phases).flatMap(([phase, cmds]) =>
    (cmds as Command[]).map((c) => `# ${phase}: ${c.description}\n${c.command}`),
  )

  const downloadMarkdown = () => {
    const lines: string[] = [`# Implementation Plan — ${clusterId}\n`]
    if (totalSavings > 0) lines.push(`Estimated savings: $${totalSavings.toFixed(0)}/month\n`)
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
          <h3 className="text-lg font-semibold text-dark-900 dark:text-white">Implementation Plan</h3>
          {totalSavings > 0 && (
            <p className="text-sm text-green-600">
              Estimated savings: ${totalSavings.toFixed(0)}/month
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
          <h4 className="mb-3 font-medium text-dark-800 dark:text-dark-200">AI Plan</h4>
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <Markdown>{markdownPlan}</Markdown>
          </div>
        </Card>
      )}

      {!hasPlan ? (
        <Card className="py-8 text-center text-dark-400">
          No implementation plan available. Run an analysis first, then generate a plan.
        </Card>
      ) : (
        Object.entries(phases).map(([phaseName, commands]) => (
          <Card key={phaseName}>
            <h4 className="mb-3 font-medium capitalize text-dark-800 dark:text-dark-200">
              {phaseName.replace(/_/g, ' ')}
              <span className="ml-2 text-sm text-dark-400">({(commands as Command[]).length} commands)</span>
            </h4>
            <div className="space-y-2">
              {(commands as Command[]).map((cmd, i) => (
                <div key={i} className="rounded-lg border border-gray-100 p-3 dark:border-dark-800">
                  <div className="flex items-start justify-between">
                    <p className="text-sm text-dark-700 dark:text-dark-300">{cmd.description}</p>
                    <Badge variant={cmd.risk_level === 'low' ? 'green' : cmd.risk_level === 'high' ? 'red' : 'yellow'}>
                      {cmd.risk_level}
                    </Badge>
                  </div>
                  <div className="mt-2 flex items-start justify-between rounded bg-gray-50 px-2 py-1 dark:bg-dark-800">
                    <code className="text-xs text-dark-600 dark:text-dark-300">{cmd.command}</code>
                    <CopyButton text={cmd.command} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ))
      )}
    </div>
  )
}
