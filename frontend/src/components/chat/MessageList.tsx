import { useEffect, useRef, useState, useCallback } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageBubble } from "./MessageBubble"
import { TypingIndicator } from "./TypingIndicator"
import { EmptyState } from "./EmptyState"
import { ScrollToBottom } from "./ScrollToBottom"
import type { Message } from "@/types"

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
  onSend: (content: string) => void
}

export function MessageList({ messages, isStreaming, onSend }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [showScrollBtn, setShowScrollBtn] = useState(false)
  const isNearBottomRef = useRef(true)

  const checkScroll = useCallback(() => {
    const viewport = scrollAreaRef.current?.querySelector(
      "[data-radix-scroll-area-viewport]"
    )
    if (!viewport) return
    const { scrollTop, scrollHeight, clientHeight } = viewport
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight
    const nearBottom = distanceFromBottom < 100
    isNearBottomRef.current = nearBottom
    setShowScrollBtn(!nearBottom)
  }, [])

  useEffect(() => {
    const viewport = scrollAreaRef.current?.querySelector(
      "[data-radix-scroll-area-viewport]"
    )
    if (!viewport) return
    viewport.addEventListener("scroll", checkScroll)
    return () => viewport.removeEventListener("scroll", checkScroll)
  }, [checkScroll])

  // Auto-scroll only when user is near the bottom
  useEffect(() => {
    if (isNearBottomRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, isStreaming])

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  if (messages.length === 0 && !isStreaming) {
    return <EmptyState onSuggestionClick={onSend} />
  }

  // Show typing indicator when streaming but no assistant text yet
  const lastMessage = messages[messages.length - 1]
  const showTyping =
    isStreaming && (!lastMessage || lastMessage.role === "user" || lastMessage.content === "")

  return (
    <div className="relative flex-1">
      <ScrollArea className="h-full p-4" ref={scrollAreaRef}>
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {showTyping && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
      <ScrollToBottom visible={showScrollBtn} onClick={scrollToBottom} />
    </div>
  )
}
