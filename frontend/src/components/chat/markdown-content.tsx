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
    <div
      className={cn(
        "prose prose-sm max-w-none leading-6 text-sm dark:prose-invert prose-slate prose-headings:font-semibold prose-headings:tracking-tight prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-1 prose-strong:font-semibold prose-code:before:content-none prose-code:after:content-none",
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          h1({ children }) {
            return <h1 className="my-3 text-lg font-semibold tracking-tight">{children}</h1>
          },
          h2({ children }) {
            return <h2 className="my-3 text-base font-semibold tracking-tight">{children}</h2>
          },
          h3({ children }) {
            return <h3 className="my-2 text-sm font-semibold tracking-tight">{children}</h3>
          },
          p({ children }) {
            return <p className="my-2 leading-6">{children}</p>
          },
          ul({ children }) {
            return <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>
          },
          ol({ children }) {
            return <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>
          },
          li({ children }) {
            return <li className="pl-1">{children}</li>
          },
          blockquote({ children }) {
            return (
              <blockquote className="my-3 rounded-r-xl border-l-4 border-primary/20 bg-primary/5 px-4 py-3 text-sm text-muted-foreground">
                {children}
              </blockquote>
            )
          },
          a({ children, href }) {
            return (
              <a
                href={href}
                className="font-medium text-primary underline underline-offset-2"
              >
                {children}
              </a>
            )
          },
          table({ children }) {
            return (
              <div className="my-3 overflow-x-auto rounded-xl border border-border/70 bg-background/80">
                <table className="min-w-full border-collapse text-sm">
                  {children}
                </table>
              </div>
            )
          },
          th({ children }) {
            return (
              <th className="border-b border-border/70 bg-muted/70 px-3 py-2 text-left font-medium text-foreground">
                {children}
              </th>
            )
          },
          td({ children }) {
            return (
              <td className="border-b border-border/50 px-3 py-2 align-top">{children}</td>
            )
          },
          code({ className, children, ...props }) {
            const isInline = !className
            if (isInline) {
              return (
                <code
                  className="rounded-md bg-muted px-1.5 py-0.5 text-[0.95em] font-mono"
                  {...props}
                >
                  {children}
                </code>
              )
            }
            return (
              <code
                className={cn(
                  "block overflow-x-auto rounded-xl bg-muted/80 p-3 text-sm",
                  className,
                )}
                {...props}
              >
                {children}
              </code>
            )
          },
          pre({ children }) {
            return <pre className="my-3 !bg-transparent !p-0">{children}</pre>
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
