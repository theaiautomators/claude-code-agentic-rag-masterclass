import { MessageSquare } from "lucide-react"

interface EmptyStateProps {
  onSuggestionClick: (text: string) => void
}

const suggestions = [
  "What can you help me with?",
  "Summarize a document for me",
  "Explain a complex topic simply",
]

export function EmptyState({ onSuggestionClick }: EmptyStateProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
        <MessageSquare className="h-6 w-6 text-muted-foreground" />
      </div>
      <div className="text-center">
        <h2 className="text-lg font-semibold">How can I help you?</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Start a conversation or try one of these suggestions
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {suggestions.map((text) => (
          <button
            key={text}
            onClick={() => onSuggestionClick(text)}
            className="rounded-full border border-border bg-background px-4 py-2 text-sm transition-colors hover:bg-muted"
          >
            {text}
          </button>
        ))}
      </div>
    </div>
  )
}
