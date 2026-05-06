import React, { createContext, useContext, useReducer, useCallback } from "react"
import type { ChatMessage, ChatSession } from "./types"
import { sendChatMessage } from "@/api/services/chat"

/* ─── State ─── */

interface ChatState {
  sessions: Record<string, ChatSession>
  currentSessionId: string | null
  isStreaming: boolean
  projectId: string | null
  bidderId: string | null
}

type Action =
  | { type: "CREATE_SESSION"; session: ChatSession }
  | { type: "DELETE_SESSION"; id: string }
  | { type: "SET_SESSION"; id: string }
  | { type: "SET_PROJECT"; id: string }
  | { type: "ADD_MESSAGE"; sessionId: string; message: ChatMessage }
  | { type: "UPDATE_LAST_MESSAGE"; sessionId: string; content: string; reasoningContent?: string }
  | { type: "ADD_TOOL_CALL"; sessionId: string; call: { name: string; result?: string } }
  | { type: "SET_STREAMING"; value: boolean }
  | { type: "SET_BIDDER"; id: string }

function chatReducer(state: ChatState, action: Action): ChatState {
  switch (action.type) {
    case "CREATE_SESSION": {
      const sessions = { ...state.sessions, [action.session.id]: action.session }
      return { ...state, sessions, currentSessionId: action.session.id }
    }
    case "DELETE_SESSION": {
      const sessions = { ...state.sessions }
      delete sessions[action.id]
      const currentSessionId = state.currentSessionId === action.id ? null : state.currentSessionId
      return { ...state, sessions, currentSessionId }
    }
    case "SET_SESSION":
      return { ...state, currentSessionId: action.id }
    case "SET_PROJECT":
      return { ...state, projectId: action.id }
    case "ADD_MESSAGE": {
      const session = state.sessions[action.sessionId]
      if (!session) return state
      return {
        ...state,
        sessions: {
          ...state.sessions,
          [action.sessionId]: {
            ...session,
            messages: [...session.messages, action.message],
            updatedAt: Date.now(),
          },
        },
      }
    }
    case "UPDATE_LAST_MESSAGE": {
      const session = state.sessions[action.sessionId]
      if (!session || session.messages.length === 0) return state
      const messages = [...session.messages]
      const last = { ...messages[messages.length - 1] }
      last.content = action.content
      if (action.reasoningContent !== undefined) {
        last.reasoningContent = (last.reasoningContent || "") + action.reasoningContent
      }
      messages[messages.length - 1] = last
      return {
        ...state,
        sessions: { ...state.sessions, [action.sessionId]: { ...session, messages } },
      }
    }
    case "ADD_TOOL_CALL": {
      const session = state.sessions[action.sessionId]
      if (!session || session.messages.length === 0) return state
      const messages = [...session.messages]
      const last = { ...messages[messages.length - 1] }
      last.toolCalls = [...(last.toolCalls || []), action.call]
      messages[messages.length - 1] = last
      return {
        ...state,
        sessions: { ...state.sessions, [action.sessionId]: { ...session, messages } },
      }
    }
    case "SET_STREAMING":
      return { ...state, isStreaming: action.value }
    case "SET_BIDDER":
      return { ...state, bidderId: action.id }
    default:
      return state
  }
}

/* ─── Context ─── */

interface ChatContextValue {
  state: ChatState
  dispatch: React.Dispatch<Action>
  currentSession: ChatSession | null
  createSession: (projectId?: string) => string
  sendMessage: (content: string) => Promise<void>
  stopStreaming: () => void
}

const ChatContext = createContext<ChatContextValue | null>(null)

function generateId() {
  return Math.random().toString(36).substring(2, 10)
}

/* ─── Provider ─── */

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, {
    sessions: {},
    currentSessionId: null,
    isStreaming: false,
    projectId: null,
    bidderId: null,
  })

  let abortControllerRef = React.useRef<AbortController | null>(null)

  const currentSession = state.currentSessionId ? state.sessions[state.currentSessionId] ?? null : null

  const createSession = useCallback(
    (projectId?: string) => {
      const id = generateId()
      const session: ChatSession = {
        id,
        projectId: projectId || state.projectId || "",
        title: `Chat ${new Date().toLocaleTimeString()}`,
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      }
      dispatch({ type: "CREATE_SESSION", session })
      return id
    },
    [state.projectId]
  )

  const sendMessage = useCallback(
    async (content: string) => {
      if (!state.currentSessionId) return
      const sessionId = state.currentSessionId

      const userMsg: ChatMessage = {
        id: generateId(),
        role: "user",
        content,
        timestamp: Date.now(),
      }
      dispatch({ type: "ADD_MESSAGE", sessionId, message: userMsg })

      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: "",
        timestamp: Date.now(),
      }
      dispatch({ type: "ADD_MESSAGE", sessionId, message: assistantMsg })
      dispatch({ type: "SET_STREAMING", value: true })

      // Build messages array from session (exclude the empty assistant message we just added)
      const session = state.sessions[sessionId]
      const historyMessages = session.messages.slice(0, -1).map((m) => ({
        role: m.role === "system" ? "system" : m.role,
        content: m.content,
        ...(m.reasoningContent ? { reasoning_content: m.reasoningContent } : {}),
      }))

      const abortController = new AbortController()
      abortControllerRef.current = abortController

      try {
        const response = await sendChatMessage(
          historyMessages,
          state.projectId || undefined,
          state.bidderId || undefined,
          abortController.signal,
        )

        if (!response.ok) throw new Error(await response.text())

        const reader = response.body!.getReader()
        const decoder = new TextDecoder()
        let fullContent = ""
        let fullReasoning = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split("\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.substring(6).trim()
              if (dataStr === "[DONE]") break

              try {
                const data = JSON.parse(dataStr)

                // Handle OpenAI-compatible format (choices array)
                if (data.choices && Array.isArray(data.choices)) {
                  const delta = data.choices[0]?.delta
                  if (delta) {
                    if (delta.content) {
                      fullContent += delta.content
                      dispatch({
                        type: "UPDATE_LAST_MESSAGE",
                        sessionId,
                        content: fullContent,
                      })
                    }
                    if (delta.reasoning_content) {
                      fullReasoning += delta.reasoning_content
                      dispatch({
                        type: "UPDATE_LAST_MESSAGE",
                        sessionId,
                        content: fullContent,
                        reasoningContent: delta.reasoning_content,
                      })
                    }
                  }
                }
                // Handle custom Hermes format (type field)
                else if (data.type) {
                  if (data.type === "content") {
                    fullContent += data.delta
                    dispatch({
                      type: "UPDATE_LAST_MESSAGE",
                      sessionId,
                      content: fullContent,
                    })
                  } else if (data.type === "thought") {
                    fullReasoning += data.delta
                    dispatch({
                      type: "UPDATE_LAST_MESSAGE",
                      sessionId,
                      content: fullContent,
                      reasoningContent: data.delta,
                    })
                  } else if (data.type === "tool_call") {
                    dispatch({
                      type: "ADD_TOOL_CALL",
                      sessionId,
                      call: { name: data.name },
                    })
                  } else if (data.type === "tool_result") {
                    dispatch({
                      type: "ADD_TOOL_CALL",
                      sessionId,
                      call: { name: data.name, result: data.result },
                    })
                  } else if (data.type === "error") {
                    dispatch({
                      type: "UPDATE_LAST_MESSAGE",
                      sessionId,
                      content: `Error: ${data.message}`,
                    })
                  }
                }
              } catch {
                // partial JSON chunk
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name !== "AbortError") {
          dispatch({
            type: "UPDATE_LAST_MESSAGE",
            sessionId,
            content: `Error: ${err.message}`,
          })
        }
      } finally {
        dispatch({ type: "SET_STREAMING", value: false })
        abortControllerRef.current = null
      }
    },
    [state.currentSessionId, state.projectId, state.sessions]
  )

  const stopStreaming = useCallback(() => {
    abortControllerRef.current?.abort()
  }, [])

  return (
    <ChatContext.Provider
      value={{ state, dispatch, currentSession, createSession, sendMessage, stopStreaming }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error("useChat must be used within ChatProvider")
  return ctx
}
