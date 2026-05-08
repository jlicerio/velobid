import { useState } from "react"
import { cn } from "@/lib/utils"
import { ChevronRight, Lightbulb } from "lucide-react"

interface ThoughtBubbleProps {
  content: string
  className?: string
}

export function ThoughtBubble({ content, className }: ThoughtBubbleProps) {
  const [open, setOpen] = useState(false)

  if (!content) return null

  return (
    <details
      open={open}
      onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
      className={cn(
        "group mb-2 rounded-xl border border-primary/10 bg-primary/5 text-xs",
        className
      )}
    >
      <summary className="flex cursor-pointer items-center gap-1.5 px-3 py-2 text-muted-foreground hover:text-foreground select-none">
        <ChevronRight
          className={cn(
            "h-3 w-3 transition-transform",
            open && "rotate-90"
          )}
        />
        <Lightbulb className="h-3 w-3" />
        <span>Thinking process</span>
      </summary>
      <div className="border-t border-primary/10 px-3 py-2 text-muted-foreground leading-relaxed whitespace-pre-wrap">
        {content}
      </div>
    </details>
  )
}
