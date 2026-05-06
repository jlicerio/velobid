import { cn } from "@/lib/utils"
import { Bot, User, Volume2, AlertCircle } from "lucide-react"
import { ThoughtBubble } from "./thought-bubble"
import { MarkdownContent } from "./markdown-content"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import type { ChatMessage } from "@/lib/types"

interface ChatMessageProps {
  message: ChatMessage
  isStreaming?: boolean
}

export function ChatMessageView({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user"
  const isSystem = message.role === "system"
  const isAssistant = message.role === "assistant"

  const handleTTS = (text: string) => {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      speechSynthesis.speak(utterance)
    }
  }

  if (isSystem) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground">
        <AlertCircle className="h-4 w-4" />
        <span>{message.content}</span>
      </div>
    )
  }

  return (
    <div className={cn("flex gap-3 px-4 py-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-medium",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-secondary text-secondary-foreground"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Content */}
      <div className={cn("flex max-w-[80%] flex-col gap-1", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-lg px-3 py-2",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted/50 text-foreground"
          )}
        >
          {isAssistant && message.reasoningContent && (
            <ThoughtBubble content={message.reasoningContent} />
          )}

          {isAssistant ? (
            <MarkdownContent content={message.content} />
          ) : (
            <div className="whitespace-pre-wrap text-sm">{message.content}</div>
          )}

          {isStreaming && !message.content && (
            <span className="inline-flex gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/40 [animation-delay:0ms]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/40 [animation-delay:150ms]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/40 [animation-delay:300ms]" />
            </span>
          )}

          {/* Tool calls */}
          {isAssistant && message.toolCalls && message.toolCalls.length > 0 && (
            <div className="mt-2 space-y-1 border-t border-border/50 pt-2">
              {message.toolCalls.map((tc, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px]">
                    {tc.name}
                  </span>
                  {tc.result && (
                    <span className="truncate max-w-[200px]" title={tc.result}>
                      {tc.result.substring(0, 60)}...
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions bar */}
        {isAssistant && message.content && (
          <div className="flex gap-1 px-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-muted-foreground"
                  onClick={() => handleTTS(message.content)}
                >
                  <Volume2 className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Read aloud</TooltipContent>
            </Tooltip>
          </div>
        )}
      </div>
    </div>
  )
}
