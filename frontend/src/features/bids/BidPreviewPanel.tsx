import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useBidPreview, formatCurrency, formatNumber } from './hooks'
import { TradeSelect } from './TradeSelect'
import { BidGenerateDialog } from './BidGenerateDialog'
import { LineItemsTable } from './LineItemsTable'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  AlertTriangle,
  ClipboardList,
  RefreshCw,
} from 'lucide-react'

export function BidPreviewPanel() {
  const { projectId } = useParams<{ projectId: string }>()
  const [trade, setTrade] = useState('hvac')
  const [showLineItems, setShowLineItems] = useState(false)

  const previewQuery = useBidPreview(
    projectId && trade ? { project_id: projectId, trade } : null,
  )

  const preview = previewQuery.data

  // Show the bid preview card & totals
  return (
    <div className="space-y-4">
      {/* Trade selector + generate */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Trade:</label>
          <TradeSelect value={trade} onChange={setTrade} />
        </div>
        <BidGenerateDialog trade={trade} />
        <Button
          variant="ghost"
          size="icon"
          onClick={() => previewQuery.refetch()}
          disabled={previewQuery.isFetching}
          title="Refresh preview"
        >
          <RefreshCw className={`h-4 w-4 ${previewQuery.isFetching ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Preview loading / error / empty */}
      {previewQuery.isLoading && (
        <Card>
          <CardContent className="py-8">
            <div className="space-y-3">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-10 w-full" />
            </div>
          </CardContent>
        </Card>
      )}

      {previewQuery.error && (
        <Card>
          <CardContent className="py-6 text-center text-muted-foreground">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-destructive" />
            <p>Failed to load bid preview.</p>
            <p className="text-sm">{(previewQuery.error as Error)?.message}</p>
          </CardContent>
        </Card>
      )}

      {preview && (
        <>
          {/* Summary + totals */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">{preview.project_name}</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {preview.bidder_name} &middot; {preview.trade_name}
                    {preview.region ? ` &middot; ${preview.region}` : ''}
                  </p>
                </div>
                <Badge variant={preview.status === 'complete' ? 'default' : 'secondary'}>
                  {preview.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {/* Validation warnings */}
              {preview.validation && preview.validation.length > 0 && (
                <div className="mb-4 rounded border border-amber-200 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-800 p-3 text-sm space-y-1">
                  <p className="font-semibold text-amber-800 dark:text-amber-300">
                    <AlertTriangle className="h-4 w-4 inline mr-1" />
                    {preview.validation.length} validation issue{preview.validation.length !== 1 ? 's' : ''}
                  </p>
                  {preview.validation.slice(0, 5).map((v, i) => (
                    <p key={i} className="text-amber-700 dark:text-amber-400">
                      <span className="font-mono text-xs">{v.field}</span>: {v.message}
                    </p>
                  ))}
                  {preview.validation.length > 5 && (
                    <p className="text-amber-600">...and {preview.validation.length - 5} more</p>
                  )}
                </div>
              )}

              {/* Totals grid */}
              <TotalsGrid
                totals={preview.totals}
              />

              {/* Exclusions */}
              {preview.exclusions.length > 0 && (
                <details className="mt-3 text-sm">
                  <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                    Exclusions ({preview.exclusions.length})
                  </summary>
                  <ul className="mt-2 space-y-0.5 list-disc list-inside text-muted-foreground">
                    {preview.exclusions.map((ex, i) => (
                      <li key={i}>{ex}</li>
                    ))}
                  </ul>
                </details>
              )}

              {/* Line items toggle */}
              <div className="mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowLineItems(!showLineItems)}
                >
                  <ClipboardList className="mr-2 h-4 w-4" />
                  {showLineItems ? 'Hide' : 'Show'} Line Items ({preview.line_items.length})
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Line items table */}
          {showLineItems && <LineItemsTable lineItems={preview.line_items} />}
        </>
      )}
    </div>
  )
}

function TotalsGrid({
  totals,
}: {
  totals: {
    total_material: number
    total_labor: number
    total_direct_cost: number
    contingency: number
    overhead_profit: number
    total_bid_amount: number
    total_labor_hours: number
    contingency_pct: number
    overhead_profit_pct: number
  }
}) {
  const rows = useMemo(
    () => [
      { label: 'Total Material', value: totals.total_material },
      { label: 'Total Labor', value: totals.total_labor },
      { label: 'Direct Cost', value: totals.total_direct_cost, bold: true },
      {
        label: `Contingency (${formatNumber(totals.contingency_pct, 1)}%)`,
        value: totals.contingency,
      },
      {
        label: `Overhead & Profit (${formatNumber(totals.overhead_profit_pct, 1)}%)`,
        value: totals.overhead_profit,
      },
      { label: 'Total Bid Amount', value: totals.total_bid_amount, bold: true, large: true },
      { label: 'Total Labor Hours', value: totals.total_labor_hours, isHours: true },
    ],
    [totals],
  )

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
      {rows.map((row) => (
        <div
          key={row.label}
          className={`rounded border p-3 ${row.bold ? 'bg-muted/50' : ''}`}
        >
          <p className="text-xs text-muted-foreground">{row.label}</p>
          <p
            className={`${
              row.large ? 'text-xl' : 'text-base'
            } font-semibold tabular-nums ${
              row.bold ? 'text-foreground' : ''
            }`}
          >
            {row.isHours ? formatNumber(row.value as number, 1) : formatCurrency(row.value as number)}
            {row.isHours ? ' hrs' : ''}
          </p>
        </div>
      ))}
    </div>
  )
}
