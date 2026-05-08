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
      <details className="px-4 py-2">
        <summary className="flex cursor-pointer items-center gap-2 rounded-xl border border-dashed border-border/70 bg-muted/20 px-3 py-2 text-xs text-muted-foreground transition-colors hover:text-foreground">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>System context</span>
          <span className="ml-auto text-[10px] uppercase tracking-[0.2em]">
            Hidden by default
          </span>
        </summary>
        <div className="mt-2 rounded-xl border border-border/70 bg-card/80 px-3 py-2 text-muted-foreground">
          <MarkdownContent
            content={message.content}
            className="text-xs prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2"
          />
        </div>
      </details>
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
      <div className={cn("flex max-w-[92%] flex-col gap-1", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl border px-4 py-3 shadow-sm",
            isUser
              ? "border-primary/20 bg-primary text-primary-foreground"
              : "border-border/70 bg-card text-foreground"
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
            <div className="mt-3 space-y-2 border-t border-border/60 pt-3">
              {message.toolCalls.map((tc, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-border/60 bg-muted/30 px-3 py-2 text-xs text-muted-foreground"
                >
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-background px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.16em] text-foreground">
                      {tc.name}
                    </span>
                    <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Tool call
                    </span>
                  </div>
                  {tc.result && (
                    <p className="mt-1 whitespace-pre-wrap break-words text-xs leading-relaxed text-muted-foreground">
                      {tc.result}
                    </p>
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
