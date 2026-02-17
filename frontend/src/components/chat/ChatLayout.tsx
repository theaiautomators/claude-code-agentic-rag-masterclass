import { useEffect } from "react"
import { useAuth } from "@/hooks/useAuth"
import { useThreads } from "@/hooks/useThreads"
import { useChat } from "@/hooks/useChat"
import { ThreadList } from "./ThreadList"
import { MessageList } from "./MessageList"
import { ChatInput } from "./ChatInput"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"

export function ChatLayout() {
  const { user, signOut } = useAuth()
  const {
    threads,
    activeThreadId,
    createThread,
    deleteThread,
    selectThread,
    updateThreadTitle,
  } = useThreads()
  const { messages, isStreaming, fetchMessages, clearMessages, sendMessage } =
    useChat()

  useEffect(() => {
    if (activeThreadId) {
      fetchMessages(activeThreadId)
    } else {
      clearMessages()
    }
  }, [activeThreadId, fetchMessages, clearMessages])

  const handleSend = async (content: string) => {
    let threadId = activeThreadId
    if (!threadId) {
      const thread = await createThread()
      threadId = thread.id
    }
    await sendMessage(threadId, content)

    // Auto-title: use first ~50 chars of first user message
    const thread = threads.find((t) => t.id === threadId)
    if (thread && thread.title === "New Chat") {
      const title = content.length > 50 ? content.slice(0, 50) + "..." : content
      updateThreadTitle(threadId, title)
    }
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="flex w-64 flex-col border-r bg-muted/30">
        <div className="flex-1 overflow-hidden">
          <ThreadList
            threads={threads}
            activeThreadId={activeThreadId}
            onSelect={selectThread}
            onCreate={() => createThread()}
            onDelete={deleteThread}
          />
        </div>
        <Separator />
        <div className="flex items-center justify-between p-3">
          <span className="truncate text-xs text-muted-foreground">
            {user?.email}
          </span>
          <Button variant="ghost" size="sm" onClick={signOut}>
            Sign out
          </Button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col">
        <MessageList messages={messages} isStreaming={isStreaming} />
        <ChatInput onSend={handleSend} disabled={isStreaming} />
      </div>
    </div>
  )
}
