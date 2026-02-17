import { useEffect, useRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageBubble } from "./MessageBubble"
import type { Message } from "@/types"

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isStreaming])

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <p>Send a message to start the conversation</p>
      </div>
    )
  }

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="mx-auto max-w-3xl space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isStreaming && (
          <div className="flex justify-start">
            <div className="rounded-lg bg-muted px-4 py-2">
              <span className="animate-pulse text-sm text-muted-foreground">
                ...
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}
