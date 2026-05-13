import React, { useState, useRef } from "react"
import { useChat } from "@/lib/chat-store"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { Send, Mic, Square } from "lucide-react"

export function MessageInput() {
  const { sendMessage, stopStreaming, state, currentSession } = useChat()
  const [text, setText] = useState("")
  const [isListening, setIsListening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const placeholder = currentSession?.projectId
    ? "Ask about the project..."
    : "Ask about the portfolio..."

  const handleSend = async () => {
    const trimmed = text.trim()
    if (!trimmed || state.isStreaming) return
    setText("")
    setError(null)
    try {
      await sendMessage(trimmed)
    } catch (err: any) {
      setText(trimmed)
      setError(err?.message || "Failed to send message")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleMic = () => {
    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
      return
    }

    if (isListening) {
      setIsListening(false)
      return
    }

    const SpeechRecognitionAPI =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (!SpeechRecognitionAPI) return

    const recognition = new SpeechRecognitionAPI()
    recognition.lang = "en-US"
    recognition.interimResults = true
    recognition.continuous = true

    recognition.onresult = (event: any) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          setText((prev) => prev + transcript)
        }
      }
    }

    recognition.onerror = () => {
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    setIsListening(true)
    recognition.start()
  }

  return (
    <div className="border-t border-border p-3">
      <div className="flex items-end gap-2">
        <div className="relative flex-1">
          <Input
            ref={inputRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="pr-10"
            disabled={state.isStreaming}
          />
        </div>

        {/* Mic button */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant={isListening ? "destructive" : "outline"}
              size="icon"
              onClick={handleMic}
              className={isListening ? "animate-pulse" : ""}
            >
              <Mic className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {isListening ? "Stop recording" : "Speech to text"}
          </TooltipContent>
        </Tooltip>

        {/* Send / Stop button */}
        {state.isStreaming ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="icon" onClick={stopStreaming}>
                <Square className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Stop generating</TooltipContent>
          </Tooltip>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="icon" onClick={handleSend} disabled={!text.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Send message</TooltipContent>
          </Tooltip>
        )}
      </div>
      {/* Error banner */}
      {error && (
        <div className="mt-2 flex items-center gap-2 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
          <span className="flex-1">{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-600 font-bold text-lg leading-none"
            aria-label="Dismiss error"
          >
            &times;
          </button>
        </div>
      )}
    </div>
  )
}
