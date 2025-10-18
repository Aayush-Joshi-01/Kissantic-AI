"use client"

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { cn } from "@/lib/utils"

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn(
      "prose prose-sm max-w-none",
      "prose-headings:font-semibold prose-headings:text-foreground",
      "prose-h1:text-xl sm:prose-h1:text-2xl prose-h1:mt-4 prose-h1:mb-3",
      "prose-h2:text-lg sm:prose-h2:text-xl prose-h2:mt-3 prose-h2:mb-2",
      "prose-h3:text-base sm:prose-h3:text-lg prose-h3:mt-3 prose-h3:mb-2",
      "prose-p:my-2 prose-p:leading-relaxed prose-p:text-foreground prose-p:text-sm sm:prose-p:text-base",
      "prose-a:text-primary prose-a:no-underline hover:prose-a:underline",
      "prose-strong:text-foreground prose-strong:font-semibold",
      "prose-code:text-primary prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs sm:prose-code:text-sm prose-code:before:content-none prose-code:after:content-none",
      "prose-pre:bg-muted prose-pre:border prose-pre:border-border prose-pre:rounded-lg prose-pre:p-3 sm:prose-pre:p-4 prose-pre:my-3 prose-pre:overflow-x-auto",
      "prose-ul:my-2 prose-ul:list-disc prose-ul:pl-4 sm:prose-ul:pl-6 prose-ul:space-y-1 prose-ul:text-sm sm:prose-ul:text-base",
      "prose-ol:my-2 prose-ol:list-decimal prose-ol:pl-4 sm:prose-ol:pl-6 prose-ol:space-y-1 prose-ol:text-sm sm:prose-ol:text-base",
      "prose-li:text-foreground prose-li:leading-relaxed prose-li:text-sm sm:prose-li:text-base",
      "prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:pl-3 sm:prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-muted-foreground prose-blockquote:my-3 prose-blockquote:text-sm sm:prose-blockquote:text-base",
      "prose-table:w-full prose-table:my-3 prose-table:border-collapse prose-table:text-xs sm:prose-table:text-sm",
      "prose-thead:bg-muted",
      "prose-th:border prose-th:border-border prose-th:px-2 sm:prose-th:px-4 prose-th:py-1.5 sm:prose-th:py-2 prose-th:text-left prose-th:font-semibold prose-th:text-foreground prose-th:text-xs sm:prose-th:text-sm",
      "prose-td:border prose-td:border-border prose-td:px-2 sm:prose-td:px-4 prose-td:py-1.5 sm:prose-td:py-2 prose-td:text-foreground prose-td:text-xs sm:prose-td:text-sm",
      "prose-tr:border-b prose-tr:border-border",
      "prose-img:rounded-lg prose-img:my-3",
      "prose-hr:my-4 prose-hr:border-border",
      className
    )}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto -mx-1 sm:mx-0 my-3 rounded-lg border border-border">
              <table className="w-full border-collapse min-w-max" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-muted" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="border border-border px-2 sm:px-4 py-1.5 sm:py-2 text-left font-semibold text-foreground text-xs sm:text-sm whitespace-nowrap" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="border border-border px-2 sm:px-4 py-1.5 sm:py-2 text-foreground text-xs sm:text-sm" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="my-2 list-disc pl-4 sm:pl-6 space-y-1 text-sm sm:text-base" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="my-2 list-decimal pl-4 sm:pl-6 space-y-1 text-sm sm:text-base" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="text-foreground leading-relaxed text-sm sm:text-base" {...props} />
          ),
          p: ({ node, ...props }) => (
            <p className="my-2 leading-relaxed text-foreground text-sm sm:text-base" {...props} />
          ),
          h1: ({ node, ...props }) => (
            <h1 className="text-xl sm:text-2xl font-semibold mt-4 mb-3 text-foreground" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-lg sm:text-xl font-semibold mt-3 mb-2 text-foreground" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-base sm:text-lg font-semibold mt-3 mb-2 text-foreground" {...props} />
          ),
          code: ({ node, inline, ...props }: any) => 
            inline ? (
              <code className="text-primary bg-muted px-1.5 py-0.5 rounded text-xs sm:text-sm" {...props} />
            ) : (
              <code className="block bg-muted border border-border rounded-lg p-3 sm:p-4 my-3 overflow-x-auto text-xs sm:text-sm" {...props} />
            ),
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-4 border-primary pl-3 sm:pl-4 italic text-muted-foreground my-3 text-sm sm:text-base" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
