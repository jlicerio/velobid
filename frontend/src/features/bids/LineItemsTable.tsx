import { useMemo, useState } from 'react'
import type { LineItemResponse } from '@/types'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { formatCurrency, formatNumber } from './hooks'

interface LineItemsTableProps {
  lineItems: LineItemResponse[]
  compact?: boolean
}

type SortField = keyof LineItemResponse
type SortDir = 'asc' | 'desc'

export function LineItemsTable({ lineItems, compact = false }: LineItemsTableProps) {
  const [sortField, setSortField] = useState<SortField>('sort_order')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [filterText, setFilterText] = useState('')
  const [pageSize, setPageSize] = useState(compact ? 10 : 25)
  const [page, setPage] = useState(0)

  const sorted = useMemo(() => {
    const filtered = filterText
      ? lineItems.filter(
          (li) =>
            li.cost_code.toLowerCase().includes(filterText.toLowerCase()) ||
            li.description.toLowerCase().includes(filterText.toLowerCase()),
        )
      : lineItems

    return [...filtered].sort((a, b) => {
      const aVal = a[sortField]
      const bVal = b[sortField]
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
      const aNum = Number(aVal) || 0
      const bNum = Number(bVal) || 0
      return sortDir === 'asc' ? aNum - bNum : bNum - aNum
    })
  }, [lineItems, sortField, sortDir, filterText])

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const paged = sorted.slice(page * pageSize, (page + 1) * pageSize)

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir('asc')
    }
    setPage(0)
  }

  function SortIcon({ field }: { field: SortField }) {
    if (sortField !== field) return <ArrowUpDown className="ml-1 h-3 w-3 inline opacity-40" />
    return sortDir === 'asc' ? (
      <ArrowUp className="ml-1 h-3 w-3 inline" />
    ) : (
      <ArrowDown className="ml-1 h-3 w-3 inline" />
    )
  }

  return (
    <div className="space-y-3">
      {/* Filter + page size controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <Input
          placeholder="Filter by code or description..."
          value={filterText}
          onChange={(e) => {
            setFilterText(e.target.value)
            setPage(0)
          }}
          className="max-w-xs h-8 text-sm"
        />
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Show</span>
          <Select
            value={String(pageSize)}
            onValueChange={(v) => {
              setPageSize(Number(v))
              setPage(0)
            }}
          >
            <SelectTrigger className="h-8 w-16">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10</SelectItem>
              <SelectItem value="25">25</SelectItem>
              <SelectItem value="50">50</SelectItem>
              <SelectItem value="100">100</SelectItem>
            </SelectContent>
          </Select>
          <span>of {sorted.length}</span>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border overflow-auto max-h-[600px]">
        <Table>
          <TableHeader className="sticky top-0 bg-background z-10">
            <TableRow>
              <SortHead field="cost_code" label="Code" onSort={handleSort} icon={<SortIcon field="cost_code" />} />
              <SortHead field="description" label="Description" onSort={handleSort} icon={<SortIcon field="description" />} />
              <SortHead field="quantity" label="Qty" onSort={handleSort} icon={<SortIcon field="quantity" />} />
              <SortHead field="unit" label="Unit" onSort={handleSort} icon={<SortIcon field="unit" />} />
              <SortHead field="unit_cost_material" label="Mat'l $/u" onSort={handleSort} icon={<SortIcon field="unit_cost_material" />} />
              <SortHead field="unit_cost_labor" label="Labor $/u" onSort={handleSort} icon={<SortIcon field="unit_cost_labor" />} />
              <SortHead field="total_material" label="Total Mat'l" onSort={handleSort} icon={<SortIcon field="total_material" />} />
              <SortHead field="total_labor" label="Total Labor" onSort={handleSort} icon={<SortIcon field="total_labor" />} />
              <SortHead field="total_phase" label="Total" onSort={handleSort} icon={<SortIcon field="total_phase" />} />
              <SortHead field="labor_hours" label="Hours" onSort={handleSort} icon={<SortIcon field="labor_hours" />} />
              <SortHead field="labor_factor" label="Factor" onSort={handleSort} icon={<SortIcon field="labor_factor" />} />
            </TableRow>
          </TableHeader>
          <TableBody>
            {paged.length === 0 ? (
              <TableRow>
                <TableCell colSpan={11} className="text-center text-muted-foreground py-8">
                  {filterText ? 'No items match filter.' : 'No line items.'}
                </TableCell>
              </TableRow>
            ) : (
              paged.map((li) => (
                <TableRow key={li.cost_code}>
                  <TableCell className="font-mono text-xs">{li.cost_code}</TableCell>
                  <TableCell className="max-w-[200px] truncate" title={li.description}>
                    {li.description}
                  </TableCell>
                  <TableCell className="text-right">{formatNumber(li.quantity, 1)}</TableCell>
                  <TableCell>{li.unit}</TableCell>
                  <TableCell className="text-right">{formatCurrency(li.unit_cost_material)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(li.unit_cost_labor)}</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(li.total_material)}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(li.total_labor)}
                  </TableCell>
                  <TableCell className="text-right font-bold">
                    {formatCurrency(li.total_phase)}
                  </TableCell>
                  <TableCell className="text-right">{formatNumber(li.labor_hours, 1)}</TableCell>
                  <TableCell className="text-right">{li.labor_factor}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Page {page + 1} of {totalPages}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-2 py-1 rounded border hover:bg-accent disabled:opacity-30"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-2 py-1 rounded border hover:bg-accent disabled:opacity-30"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

/* Sortable header cell helper */
function SortHead({
  field,
  label,
  onSort,
  icon,
}: {
  field: SortField
  label: string
  onSort: (field: SortField) => void
  icon: React.ReactNode
}) {
  return (
    <TableHead
      className="cursor-pointer select-none whitespace-nowrap"
      onClick={() => onSort(field)}
    >
      {label} {icon}
    </TableHead>
  )
}
