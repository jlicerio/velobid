import { useChat } from "@/lib/chat-store"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { MessageSquare, Plus, Trash2, PanelLeftClose, PanelLeft } from "lucide-react"
import { cn } from "@/lib/utils"

interface SessionSidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export function SessionSidebar({ collapsed, onToggle }: SessionSidebarProps) {
  const { state, dispatch, createSession } = useChat()
  const sessions = Object.values(state.sessions)

  const handleNewSession = () => {
    const id = createSession()
    dispatch({ type: "SET_SESSION", id })
  }

  if (collapsed) {
    return (
      <div className="flex flex-col items-center gap-2 border-r border-border bg-muted/20 p-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" onClick={onToggle} className="h-8 w-8">
              <PanelLeft className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">Expand sidebar</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" onClick={handleNewSession} className="h-8 w-8">
              <Plus className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">New chat</TooltipContent>
        </Tooltip>

        {sessions.slice(-3).map((s) => (
          <Tooltip key={s.id}>
            <TooltipTrigger asChild>
              <Button
                variant={state.currentSessionId === s.id ? "secondary" : "ghost"}
                size="icon"
                className="h-8 w-8"
                onClick={() => dispatch({ type: "SET_SESSION", id: s.id })}
              >
                <MessageSquare className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-[200px]">
              <p className="truncate">{s.title}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    )
  }

  return (
    <div className="flex w-52 flex-col border-r border-border bg-muted/10">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <span className="text-xs font-medium text-muted-foreground">History</span>
        <div className="flex gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleNewSession}>
                <Plus className="h-3.5 w-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>New chat</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onToggle}>
                <PanelLeftClose className="h-3.5 w-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Collapse sidebar</TooltipContent>
          </Tooltip>
        </div>
      </div>

      {/* Session list */}
      <ScrollArea className="flex-1">
        <div className="space-y-0.5 p-2">
          {sessions.length === 0 && (
            <p className="px-2 py-4 text-center text-xs text-muted-foreground">
              No chat sessions yet
            </p>
          )}
          {[...sessions]
            .sort((a, b) => b.updatedAt - a.updatedAt)
            .map((session) => (
              <div
                key={session.id}
                className={cn(
                  "group flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-accent",
                  state.currentSessionId === session.id && "bg-accent"
                )}
                onClick={() => dispatch({ type: "SET_SESSION", id: session.id })}
              >
                <MessageSquare className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                <span className="flex-1 truncate text-xs">{session.title}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 opacity-0 group-hover:opacity-100"
                  onClick={(e) => {
                    e.stopPropagation()
                    dispatch({ type: "DELETE_SESSION", id: session.id })
                  }}
                >
                  <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
                </Button>
              </div>
            ))}
        </div>
      </ScrollArea>
    </div>
  )
}
