import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import { cn } from "@/lib/utils"

interface MarkdownContentProps {
  content: string
  className?: string
}

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  if (!content) return null

  return (
    <div className={cn("prose prose-sm max-w-none dark:prose-invert prose-code:before:content-none prose-code:after:content-none", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          table({ children }) {
            return (
              <div className="overflow-x-auto my-2">
                <table className="min-w-full border-collapse border border-border text-sm">
                  {children}
                </table>
              </div>
            )
          },
          th({ children }) {
            return (
              <th className="border border-border bg-muted px-3 py-1.5 text-left font-medium">
                {children}
              </th>
            )
          },
          td({ children }) {
            return (
              <td className="border border-border px-3 py-1.5">{children}</td>
            )
          },
          code({ className, children, ...props }) {
            const isInline = !className
            if (isInline) {
              return (
                <code className="rounded bg-muted px-1 py-0.5 text-sm font-mono" {...props}>
                  {children}
                </code>
              )
            }
            return (
              <code className={cn("block rounded-lg bg-muted p-3 text-sm overflow-x-auto", className)} {...props}>
                {children}
              </code>
            )
          },
          pre({ children }) {
            return <pre className="!bg-transparent !p-0">{children}</pre>
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
