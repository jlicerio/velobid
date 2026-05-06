import React, { useEffect, useRef, useState } from "react"
import { useChat } from "@/lib/chat-store"
import { ChatMessageView } from "./chat-message"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageSquare } from "lucide-react"

export function MessageList() {
  const { currentSession, state } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  const messages = currentSession?.messages ?? []

  // Auto-scroll on new messages
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages.length, messages[messages.length - 1]?.content, autoScroll])

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100
    setAutoScroll(isNearBottom)
  }

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 text-muted-foreground">
        <MessageSquare className="h-12 w-12 opacity-20" />
        <p className="text-sm">Start a conversation with the AI assistant</p>
        <p className="text-xs">Ask about project pricing, materials, or generate bids</p>
      </div>
    )
  }

  return (
    <ScrollArea
      className="flex-1"
      onScroll={handleScroll}
    >
      <div className="py-2">
        {messages.map((msg, idx) => (
          <ChatMessageView
            key={msg.id}
            message={msg}
            isStreaming={
              state.isStreaming &&
              idx === messages.length - 1 &&
              msg.role === "assistant"
            }
          />
        ))}
      </div>
      <div ref={bottomRef} />
    </ScrollArea>
  )
}
