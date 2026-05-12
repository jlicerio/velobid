import React, { createContext, useContext, useReducer, useCallback } from "react"
import type { ChatMessage, ChatSession, StreamError } from "./types"
import { sendChatMessage } from "@/api/services/chat"
import { fetchProjectsWithPricing } from "@/api/services/projects"
import {
  buildDashboardContext,
  loadDashboardSnapshot,
  type DashboardSnapshot,
} from "@/lib/dashboard-context"

/* ─── State ─── */

interface ChatState {
  sessions: Record<string, ChatSession>
  currentSessionId: string | null
  isStreaming: boolean
  projectId: string | null
  bidderId: string | null
  dashboardSnapshot: DashboardSnapshot | null
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
  | { type: "SET_DASHBOARD_SNAPSHOT"; snapshot: DashboardSnapshot | null }
  | { type: "SET_STREAM_ERROR"; sessionId: string; error: StreamError }
  | { type: "CLEAR_STREAM_ERROR"; sessionId: string }

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
    case "SET_DASHBOARD_SNAPSHOT":
      return { ...state, dashboardSnapshot: action.snapshot }
    case "SET_STREAM_ERROR": {
      const session = state.sessions[action.sessionId]
      if (!session) return state
      return {
        ...state,
        sessions: {
          ...state.sessions,
          [action.sessionId]: { ...session, streamError: action.error },
        },
      }
    }
    case "CLEAR_STREAM_ERROR": {
      const session = state.sessions[action.sessionId]
      if (!session) return state
      return {
        ...state,
        sessions: {
          ...state.sessions,
          [action.sessionId]: { ...session, streamError: null },
        },
      }
    }
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

async function buildProjectContext(projectId?: string | null): Promise<string | null> {
  if (!projectId) return null

  try {
    const projects = await fetchProjectsWithPricing()
    const project = projects.find((p) => p.id === projectId)
    if (!project) return null

    const location = [project.city, project.state].filter(Boolean).join(", ")
    const lines = [
      "# Project Context",
      "",
      `- Project: ${project.name}`,
      location ? `- Location: ${location}` : null,
      `- Trade: ${project.trade || "unknown"}`,
      "",
      "## Bid Snapshot",
      project.total_bid != null
        ? `- Current bid total: $${project.total_bid.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        : "- Current bid total: unavailable",
      project.total_labor_hours != null
        ? `- Labor hours: ${project.total_labor_hours.toLocaleString()} hrs`
        : "- Labor hours: unavailable",
      project.total_labor != null
        ? `- Labor cost: $${project.total_labor.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        : "- Labor cost: unavailable",
      project.total_material != null
        ? `- Material cost: $${project.total_material.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        : "- Material cost: unavailable",
      project.area_sf != null
        ? `- Area: ${project.area_sf.toLocaleString()} SF`
        : "- Area: unavailable",
      "",
      "## Guidance",
      "Use the project context above when answering questions about the current bid, especially bid total, labor hours, material cost, and scope.",
      "If the user asks for the current bid total, answer with the current bid total.",
      "If they ask for labor hours, answer with the labor hours.",
    ]

    return lines.filter(Boolean).join("\n")
  } catch {
    return null
  }
}

/* ─── Provider ─── */

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, {
    sessions: {},
    currentSessionId: null,
    isStreaming: false,
    projectId: null,
    bidderId: null,
    dashboardSnapshot: null,
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

      // Build messages from the current session history and include the new user message.
      const session = state.sessions[sessionId]
      const priorMessages = session?.messages ?? []
      const historyMessages = [...priorMessages, userMsg].map((m) => ({
        role: m.role === "system" ? "system" : m.role,
        content: m.content,
        ...(m.reasoningContent ? { reasoning_content: m.reasoningContent } : {}),
      }))

      const abortController = new AbortController()
      abortControllerRef.current = abortController

      try {
        const hasProjectContext = Boolean(session.projectId || state.projectId)
        let outboundMessages = historyMessages

        if (hasProjectContext) {
          const projectContext = await buildProjectContext(
            session.projectId || state.projectId || null,
          )
          if (projectContext) {
            outboundMessages = [{ role: "system", content: projectContext }, ...historyMessages]
          }
        } else {
          const dashboardSnapshot =
            state.dashboardSnapshot ?? (await loadDashboardSnapshot())

          if (dashboardSnapshot) {
            if (!state.dashboardSnapshot) {
              dispatch({ type: "SET_DASHBOARD_SNAPSHOT", snapshot: dashboardSnapshot })
            }

            outboundMessages = [
              { role: "system", content: buildDashboardContext(dashboardSnapshot) },
              ...historyMessages,
            ]
          }
        }

        const response = await sendChatMessage(
          outboundMessages,
          state.projectId || undefined,
          state.bidderId || undefined,
          abortController.signal,
        )

        if (!response.ok) {
          let message = `Request failed (${response.status})`
          try {
            const payload = await response.json()
            const detail = payload?.detail
            if (typeof detail === "string") {
              message = detail
            } else if (detail?.message) {
              message = detail.message
              if (detail.retry_after_seconds) {
                message += ` Retry in ${detail.retry_after_seconds}s.`
              }
            }
          } catch {
            const fallback = await response.text()
            if (fallback) message = fallback
          }
          throw new Error(message)
        }

        const reader = response.body!.getReader()
        const decoder = new TextDecoder()
        let fullContent = ""
        let fullReasoning = ""
        let receivedMeaningfulEvent = false

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
                      receivedMeaningfulEvent = true
                      fullContent += delta.content
                      dispatch({
                        type: "UPDATE_LAST_MESSAGE",
                        sessionId,
                        content: fullContent,
                      })
                    }
                    if (delta.reasoning_content) {
                      receivedMeaningfulEvent = true
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
                    receivedMeaningfulEvent = true
                    fullContent += data.delta
                    dispatch({
                      type: "UPDATE_LAST_MESSAGE",
                      sessionId,
                      content: fullContent,
                    })
                  } else if (data.type === "thought") {
                    receivedMeaningfulEvent = true
                    fullReasoning += data.delta
                    dispatch({
                      type: "UPDATE_LAST_MESSAGE",
                      sessionId,
                      content: fullContent,
                      reasoningContent: data.delta,
                    })
                  } else if (data.type === "tool_call") {
                    receivedMeaningfulEvent = true
                    dispatch({
                      type: "ADD_TOOL_CALL",
                      sessionId,
                      call: { name: data.name },
                    })
                  } else if (data.type === "tool_result") {
                    receivedMeaningfulEvent = true
                    dispatch({
                      type: "ADD_TOOL_CALL",
                      sessionId,
                      call: { name: data.name, result: data.result },
                    })
                  } else if (data.type === "error") {
                    receivedMeaningfulEvent = true
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

        // If the stream ended ([DONE]) without delivering any meaningful content,
        // update the assistant message with a diagnostic.
        if (!receivedMeaningfulEvent) {
          dispatch({
            type: "UPDATE_LAST_MESSAGE",
            sessionId,
            content:
              "The AI assistant returned an empty response. This may indicate a temporary issue with the AI service. Please try again.",
          })
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
    [
      state.currentSessionId,
      state.projectId,
      state.sessions,
      state.bidderId,
      state.dashboardSnapshot,
    ]
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
