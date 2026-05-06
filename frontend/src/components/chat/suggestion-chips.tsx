import { useChat } from "@/lib/chat-store"
import { Button } from "@/components/ui/button"

const SUGGESTIONS = [
  "What's the current bid total?",
  "Show me the line items",
  "Update material cost by 5%",
  "Generate the bid package",
  "Compare with previous version",
]

interface SuggestionChipsProps {
  onSelect: (text: string) => void
}

export function SuggestionChips({ onSelect }: SuggestionChipsProps) {
  const { currentSession, state } = useChat()
  const hasMessages = (currentSession?.messages.length ?? 0) > 0

  // Only show suggestions when no messages yet (and not streaming)
  if (hasMessages || state.isStreaming) return null

  return (
    <div className="flex flex-wrap gap-1.5 px-3 py-2 overflow-hidden max-w-full">
      {SUGGESTIONS.map((suggestion) => (
        <Button
          key={suggestion}
          variant="outline"
          size="sm"
          className="text-[11px] text-muted-foreground hover:text-foreground truncate max-w-full leading-tight h-auto py-1"
          onClick={() => onSelect(suggestion)}
        >
          {suggestion}
        </Button>
      ))}
    </div>
  )
}
