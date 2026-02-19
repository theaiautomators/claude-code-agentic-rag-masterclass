import { useEffect, useState } from "react"
import { useAuth } from "@/hooks/useAuth"
import { useThreads } from "@/hooks/useThreads"
import { useChat } from "@/hooks/useChat"
import { ThreadList } from "./ThreadList"
import { MessageList } from "./MessageList"
import { ChatInput } from "./ChatInput"
import { SettingsPage } from "@/components/settings/SettingsPage"
import { DebugPage } from "@/components/debug/DebugPage"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { MessageSquare, Settings, Bug } from "lucide-react"

type Page = "chat" | "settings" | "debug"

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

  const [activePage, setActivePage] = useState<Page>("chat")

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

  const navItems: { page: Page; icon: typeof MessageSquare; label: string }[] = [
    { page: "chat", icon: MessageSquare, label: "Chat" },
    { page: "settings", icon: Settings, label: "Settings" },
    { page: "debug", icon: Bug, label: "Debug" },
  ]

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="flex w-64 flex-col border-r bg-muted/30">
        {/* Thread list — visible on all pages, clicking a thread switches to chat */}
        <div className="flex-1 overflow-hidden">
          <ThreadList
            threads={threads}
            activeThreadId={activePage === "chat" ? activeThreadId : null}
            onSelect={(id) => {
              selectThread(id)
              setActivePage("chat")
            }}
            onCreate={() => {
              createThread()
              setActivePage("chat")
            }}
            onDelete={deleteThread}
          />
        </div>

        <Separator />

        {/* Navigation */}
        <div className="flex items-center justify-center gap-1 px-3 py-2">
          {navItems.map(({ page, icon: Icon, label }) => (
            <Button
              key={page}
              variant={activePage === page ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActivePage(page)}
              className="flex-1 gap-1.5"
              title={label}
            >
              <Icon className="h-4 w-4" />
              <span className="text-xs">{label}</span>
            </Button>
          ))}
        </div>

        <Separator />

        {/* User footer */}
        <div className="flex items-center justify-between p-3">
          <span className="truncate text-xs text-muted-foreground">
            {user?.email}
          </span>
          <Button variant="ghost" size="sm" onClick={signOut} disabled>
            Sign out
          </Button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col">
        {activePage === "chat" && (
          <>
            <MessageList messages={messages} isStreaming={isStreaming} />
            <ChatInput onSend={handleSend} disabled={isStreaming} />
          </>
        )}
        {activePage === "settings" && <SettingsPage />}
        {activePage === "debug" && <DebugPage />}
      </div>
    </div>
  )
}
