import { useChat } from "@/lib/chat-store"
import { Button } from "@/components/ui/button"

const GENERAL_SUGGESTIONS = [
  "What's the current bid total?",
  "Show me the line items",
  "Update material cost by 5%",
  "Generate the bid package",
  "Compare with previous version",
]

const PROJECT_SUGGESTIONS = [
  "What's the current bid total for this project?",
  "How many labor hours are on this project?",
  "Summarize the major cost drivers",
  "Show me the line items",
  "Compare with previous version",
]

const DASHBOARD_SUGGESTIONS = [
  "Give me a portfolio overview",
  "Which projects are highest value?",
  "Show active and archived project counts",
  "Which projects have the most labor hours?",
  "What projects need attention?",
]

interface SuggestionChipsProps {
  onSelect: (text: string) => void
}

export function SuggestionChips({ onSelect }: SuggestionChipsProps) {
  const { currentSession, state } = useChat()
  const hasMessages = (currentSession?.messages.length ?? 0) > 0
  const suggestions = currentSession
    ? currentSession.projectId
      ? PROJECT_SUGGESTIONS
      : DASHBOARD_SUGGESTIONS
    : GENERAL_SUGGESTIONS

  // Only show suggestions when no messages yet (and not streaming)
  if (hasMessages || state.isStreaming) return null

  return (
    <div className="flex flex-wrap gap-1.5 px-3 py-2 overflow-hidden max-w-full">
      {suggestions.map((suggestion) => (
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
