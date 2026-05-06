export interface ChatMessage {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  reasoningContent?: string
  timestamp: number
  toolCalls?: ToolCallInfo[]
}

export interface ToolCallInfo {
  name: string
  result?: string
}

export interface ChatSession {
  id: string
  projectId: string
  title: string
  messages: ChatMessage[]
  createdAt: number
  updatedAt: number
}

export interface SSEEvent {
  type: "content" | "thought" | "tool_call" | "tool_result" | "error"
  delta?: string
  name?: string
  result?: string
  message?: string
}
