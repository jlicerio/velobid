import { useChat } from "@/lib/chat-store"
import { Button } from "@/components/ui/button"

const PROJECT_SUGGESTIONS = [
  "What's the current bid total for this project?",
  "How many labor hours are on this project?",
  "Summarize the major cost drivers",
  "Show me the line items",
  "Compare with previous version",
]

const DASHBOARD_SUGGESTIONS = [
  "Portfolio overview",
  "Highest value projects",
  "Active vs archived",
  "Most labor hours",
  "Projects needing attention",
]

interface SuggestionChipsProps {
  onSelect: (text: string) => void
}

export function SuggestionChips({ onSelect }: SuggestionChipsProps) {
  const { currentSession, state } = useChat()
  const hasMessages = (currentSession?.messages.length ?? 0) > 0
  const suggestions = currentSession?.projectId
    ? PROJECT_SUGGESTIONS
    : DASHBOARD_SUGGESTIONS

  // Only show suggestions when no messages yet (and not streaming)
  if (hasMessages || state.isStreaming) return null

  return (
    <div className="mx-3 mb-2 flex max-w-full flex-wrap gap-2 overflow-hidden rounded-2xl border border-border/60 bg-background/70 px-3 py-2">
      {suggestions.map((suggestion) => (
        <Button
          key={suggestion}
          variant="outline"
          size="sm"
          className="h-auto max-w-full truncate rounded-full border-border/70 bg-card/80 px-3 py-1 text-[11px] font-medium text-muted-foreground shadow-sm transition-colors hover:text-foreground hover:bg-primary/5"
          onClick={() => onSelect(suggestion)}
        >
          {suggestion}
        </Button>
      ))}
    </div>
  )
}
