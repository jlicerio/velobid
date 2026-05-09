import React, { useState, useCallback } from "react"
import { useChat } from "@/lib/chat-store"
import { SessionSidebar } from "./session-sidebar"
import { MessageList } from "./message-list"
import { MessageInput } from "./message-input"
import { SuggestionChips } from "./suggestion-chips"
import { DashboardSnapshotCard } from "./dashboard-snapshot"
import { cn } from "@/lib/utils"

interface ChatPanelProps {
  className?: string
}

export function ChatPanel({ className }: ChatPanelProps) {
  const { state, currentSession, createSession, dispatch, sendMessage } = useChat()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true)

  // Ensure a session exists
  React.useEffect(() => {
    if (!state.currentSessionId) {
      const id = createSession()
      dispatch({ type: "SET_SESSION", id })
    }
  }, [])

  const handleSuggestionSelect = useCallback(
    (text: string) => {
      // Create a new session if one doesn't exist
      if (!currentSession) {
        const id = createSession()
        dispatch({ type: "SET_SESSION", id })
      }
      sendMessage(text)
    },
    [currentSession, createSession, dispatch, sendMessage]
  )

  return (
    <div className={cn("flex h-full", className)}>
      {/* Session sidebar */}
      <SessionSidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center border-b border-border px-4 py-2">
          <span className="text-xs text-muted-foreground">
            {currentSession?.projectId ? `Project: ${currentSession.projectId}` : "Portfolio overview"}
          </span>
        </div>

        {!currentSession?.projectId && state.dashboardSnapshot && (
          <DashboardSnapshotCard snapshot={state.dashboardSnapshot} />
        )}

        {/* Messages */}
        <MessageList />

        {/* Suggestion chips */}
        <SuggestionChips onSelect={handleSuggestionSelect} />

        {/* Input */}
        <MessageInput />
      </div>
    </div>
  )
}
