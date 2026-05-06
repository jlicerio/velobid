import { useTrades } from './hooks'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface TradeSelectProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function TradeSelect({ value, onChange, disabled }: TradeSelectProps) {
  const { data: trades, isLoading } = useTrades()

  return (
    <Select
      value={value}
      onValueChange={onChange}
      disabled={disabled || isLoading}
    >
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder={isLoading ? 'Loading trades...' : 'Select trade'} />
      </SelectTrigger>
      <SelectContent>
        {trades?.map((trade) => (
          <SelectItem key={trade.id} value={trade.id}>
            {trade.name || trade.id}
          </SelectItem>
        ))}
        {trades && trades.length === 0 && (
          <SelectItem value="__none__" disabled>
            No trades available
          </SelectItem>
        )}
      </SelectContent>
    </Select>
  )
}
