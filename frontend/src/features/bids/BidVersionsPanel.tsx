import { useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import {
  useVersionsList,
  useVersionDetail,
  useVersionDiff,
  useCreateVersion,
  useRestoreVersion,
  formatCurrency,
} from './hooks'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import {
  GitBranch,
  Plus,
  RotateCcw,
  Eye,
  ArrowUpDown,
  FileClock,
} from 'lucide-react'
import { toast } from 'sonner'
import { LineItemsTable } from './LineItemsTable'
import type { VersionMetadata, VersionDiff } from '@/types'

interface BidVersionsPanelProps {
  trade: string
}

export function BidVersionsPanel({ trade }: BidVersionsPanelProps) {
  const { projectId } = useParams<{ projectId: string }>()
  const [viewVersion, setViewVersion] = useState<string | null>(null)
  const [diffVersion, setDiffVersion] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [commitMessage, setCommitMessage] = useState('')

  const versionsQuery = useVersionsList(projectId || '', trade)
  const versionDetailQuery = useVersionDetail(projectId || '', trade, viewVersion)
  const versionDiffQuery = useVersionDiff(projectId || '', trade, diffVersion)
  const createVersion = useCreateVersion(projectId || '', trade)
  const restoreVersion = useRestoreVersion(projectId || '', trade)

  const versions = versionsQuery.data?.versions ?? []

  const handleCreate = useCallback(async () => {
    if (!projectId) return
    try {
      await createVersion.mutateAsync({
        trigger_source: 'user_edit',
        commit_message: commitMessage || undefined,
      })
      toast.success('Version snapshot created')
      setShowCreate(false)
      setCommitMessage('')
    } catch {
      toast.error('Failed to create snapshot')
    }
  }, [projectId, commitMessage, createVersion])

  const handleRestore = useCallback(
    async (versionId: string) => {
      if (!confirm('Restore this version? Current bid data will be replaced.')) return
      try {
        await restoreVersion.mutateAsync(versionId)
        toast.success(`Version ${versionId} restored`)
      } catch {
        toast.error('Failed to restore version')
      }
    },
    [restoreVersion],
  )

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <GitBranch className="h-5 w-5" />
          Bid Versions
        </h3>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="mr-1 h-4 w-4" />
          Snapshot
        </Button>
      </div>

      {/* Loading */}
      {versionsQuery.isLoading && (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      )}

      {/* Empty */}
      {!versionsQuery.isLoading && versions.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            <FileClock className="h-8 w-8 mx-auto mb-2" />
            <p>No version snapshots yet.</p>
            <p className="text-sm">Generate a bid snapshot to track changes over time.</p>
          </CardContent>
        </Card>
      )}

      {/* Version list */}
      {versions.length > 0 && (
        <div className="space-y-2">
          {[...versions].reverse().map((v: VersionMetadata) => (
            <Card key={v.version_id} className="hover:bg-muted/30 transition-colors">
              <CardContent className="py-3 flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="font-mono text-xs">
                      {v.version_id}
                    </Badge>
                    <span className="text-sm font-medium truncate">
                      {v.commit_message || v.trigger_source}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {new Date(v.timestamp).toLocaleString()} &middot;{' '}
                    <span className="italic">{v.trigger_source}</span>
                    {v.snapshot_summary && <> &middot; {v.snapshot_summary}</>}
                  </p>
                </div>
                <div className="flex gap-1 shrink-0 ml-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setViewVersion(v.version_id)}
                    title="View details"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDiffVersion(v.version_id)}
                    title="View diff"
                  >
                    <ArrowUpDown className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRestore(v.version_id)}
                    disabled={restoreVersion.isPending}
                    title="Restore this version"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create snapshot dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Version Snapshot</DialogTitle>
            <DialogDescription>
              Save the current bid state as a named version.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <label className="text-sm font-medium">Commit message (optional)</label>
            <Textarea
              placeholder="e.g. Adjusted material costs per supplier quote"
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={createVersion.isPending}>
              {createVersion.isPending ? 'Saving...' : 'Create Snapshot'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View version detail dialog */}
      <Dialog
        open={!!viewVersion}
        onOpenChange={(o) => { if (!o) setViewVersion(null) }}
      >
        <DialogContent className="sm:max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Version {versionDetailQuery.data?.version_id}
            </DialogTitle>
            <DialogDescription>
              {versionDetailQuery.data?.commit_message}
              &nbsp;&middot;&nbsp;
              {versionDetailQuery.data?.timestamp
                ? new Date(versionDetailQuery.data.timestamp).toLocaleString()
                : ''}
            </DialogDescription>
          </DialogHeader>
          {versionDetailQuery.isLoading && <Skeleton className="h-40 w-full" />}
          {versionDetailQuery.data && (
            <div className="space-y-4">
              {/* Totals */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {Object.entries(
                  versionDetailQuery.data.snapshot_data.totals as Record<string, number>,
                ).map(([key, val]) => (
                  <div key={key} className="rounded border p-2 text-sm">
                    <p className="text-xs text-muted-foreground">
                      {key.replace(/_/g, ' ')}
                    </p>
                    <p className="font-semibold tabular-nums">
                      {typeof val === 'number' ? formatCurrency(val) : String(val)}
                    </p>
                  </div>
                ))}
              </div>
              {/* Line items (read-only) */}
              <details>
                <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">
                  Line items (
                  {(
                    versionDetailQuery.data.snapshot_data.line_items as Record<string, unknown>[]
                  ).length}
                  )
                </summary>
                <div className="mt-2">
                  <LineItemsTable
                    lineItems={
                      versionDetailQuery.data.snapshot_data
                        .line_items as unknown as any[]
                    }
                    compact
                  />
                </div>
              </details>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewVersion(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Diff dialog */}
      <Dialog
        open={!!diffVersion}
        onOpenChange={(o) => { if (!o) setDiffVersion(null) }}
      >
        <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Diff: {diffVersion}
              {versionDiffQuery.data?.diff?.from_version
                ? ` vs ${versionDiffQuery.data.diff.from_version}`
                : ''}
            </DialogTitle>
          </DialogHeader>
          {versionDiffQuery.isLoading && <Skeleton className="h-32 w-full" />}
          {versionDiffQuery.data?.diff && (
            <DiffDisplay diff={versionDiffQuery.data.diff} />
          )}
          {versionDiffQuery.data?.diff === null && (
            <p className="text-muted-foreground text-sm py-4">
              This is the initial version — no previous version to compare.
            </p>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDiffVersion(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function DiffDisplay({ diff }: { diff: VersionDiff }) {
  return (
    <div className="space-y-4 text-sm">
      {/* Summary */}
      <p className="font-medium">{diff.summary}</p>

      {/* Totals changed */}
      {Object.keys(diff.totals_changed).length > 0 && (
        <div>
          <h4 className="font-semibold text-sm mb-1">Totals Changed</h4>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="text-left py-1">Field</th>
                <th className="text-right py-1">From</th>
                <th className="text-right py-1">To</th>
                <th className="text-right py-1">Delta</th>
                <th className="text-right py-1">%</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(diff.totals_changed).map(([key, td]) => (
                <tr key={key} className="border-b last:border-0">
                  <td className="py-1 capitalize">{key.replace(/_/g, ' ')}</td>
                  <td className="text-right py-1 tabular-nums">
                    {formatCurrency(td.from)}
                  </td>
                  <td className="text-right py-1 tabular-nums">
                    {formatCurrency(td.to)}
                  </td>
                  <td
                    className={`text-right py-1 tabular-nums ${
                      td.delta >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {td.delta >= 0 ? '+' : ''}
                    {formatCurrency(td.delta)}
                  </td>
                  <td
                    className={`text-right py-1 tabular-nums ${
                      td.delta_pct >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {td.delta_pct >= 0 ? '+' : ''}
                    {td.delta_pct.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Line items changed */}
      {diff.line_items_changed.length > 0 && (
        <div>
          <h4 className="font-semibold text-sm mb-1">Line Items Changed ({diff.line_items_changed.length})</h4>
          <div className="max-h-48 overflow-y-auto space-y-1">
            {diff.line_items_changed.map((ch, i) => (
              <div key={i} className="rounded border p-2 text-xs">
                <span className="font-mono">{ch.cost_code}</span>
                &nbsp;{ch.description}&nbsp;&middot;&nbsp;
                <span className="italic">{ch.field}</span>:{' '}
                <span className="text-red-600 line-through">{String(ch.from)}</span>
                &rarr;
                <span className="text-green-600">{String(ch.to)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Added/removed items */}
      {diff.line_items_added.length > 0 && (
        <p className="text-green-600">
          + {diff.line_items_added.length} line item{diff.line_items_added.length !== 1 ? 's' : ''} added
        </p>
      )}
      {diff.line_items_removed.length > 0 && (
        <p className="text-red-600">
          - {diff.line_items_removed.length} line item{diff.line_items_removed.length !== 1 ? 's' : ''} removed
        </p>
      )}
    </div>
  )
}
