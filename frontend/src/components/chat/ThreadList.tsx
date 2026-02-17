import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import type { Thread } from "@/types"

interface ThreadListProps {
  threads: Thread[]
  activeThreadId: string | null
  onSelect: (threadId: string) => void
  onCreate: () => void
  onDelete: (threadId: string) => void
}

export function ThreadList({
  threads,
  activeThreadId,
  onSelect,
  onCreate,
  onDelete,
}: ThreadListProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="p-3">
        <Button onClick={onCreate} className="w-full" variant="outline">
          + New Chat
        </Button>
      </div>
      <Separator />
      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {threads.map((thread) => (
            <div
              key={thread.id}
              className={`group flex cursor-pointer items-center justify-between rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent ${
                thread.id === activeThreadId
                  ? "bg-accent text-accent-foreground"
                  : ""
              }`}
              onClick={() => onSelect(thread.id)}
            >
              <span className="truncate">{thread.title}</span>
              <button
                className="ml-2 hidden text-muted-foreground hover:text-destructive group-hover:inline"
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete(thread.id)
                }}
              >
                &times;
              </button>
            </div>
          ))}
          {threads.length === 0 && (
            <p className="px-3 py-2 text-sm text-muted-foreground">
              No conversations yet
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
