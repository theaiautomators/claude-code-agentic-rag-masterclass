import { useState, useCallback } from "react"
import { apiGet, apiStreamPost } from "@/lib/api"
import type { Message } from "@/types"

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [loading, setLoading] = useState(false)

  const fetchMessages = useCallback(async (threadId: string) => {
    setLoading(true)
    try {
      const data = await apiGet<{ messages: Message[] }>(
        `/chat/${threadId}/messages`,
      )
      setMessages(data.messages)
    } catch (err) {
      console.error("Failed to fetch messages:", err)
    } finally {
      setLoading(false)
    }
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  const sendMessage = async (threadId: string, content: string) => {
    // Optimistically add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      thread_id: threadId,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Add placeholder assistant message for streaming
    const assistantId = crypto.randomUUID()
    const assistantMessage: Message = {
      id: assistantId,
      thread_id: threadId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, assistantMessage])
    setIsStreaming(true)

    await apiStreamPost(
      `/chat/${threadId}/messages`,
      { content },
      // onDelta
      (delta) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: m.content + delta } : m,
          ),
        )
      },
      // onDone
      () => {
        setIsStreaming(false)
      },
      // onError
      (error) => {
        console.error("Stream error:", error)
        setIsStreaming(false)
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: "An error occurred. Please try again." }
              : m,
          ),
        )
      },
    )
  }

  return {
    messages,
    isStreaming,
    loading,
    fetchMessages,
    clearMessages,
    sendMessage,
  }
}
