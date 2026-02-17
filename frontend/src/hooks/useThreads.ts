import { useState, useEffect, useCallback } from "react"
import { apiGet, apiPost, apiDelete } from "@/lib/api"
import type { Thread } from "@/types"

export function useThreads() {
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchThreads = useCallback(async () => {
    try {
      const data = await apiGet<{ threads: Thread[] }>("/threads/")
      setThreads(data.threads)
    } catch (err) {
      console.error("Failed to fetch threads:", err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchThreads()
  }, [fetchThreads])

  const createThread = async (title?: string) => {
    const thread = await apiPost<Thread>("/threads/", { title: title || "New Chat" })
    setThreads((prev) => [thread, ...prev])
    setActiveThreadId(thread.id)
    return thread
  }

  const deleteThread = async (threadId: string) => {
    await apiDelete(`/threads/${threadId}`)
    setThreads((prev) => prev.filter((t) => t.id !== threadId))
    if (activeThreadId === threadId) {
      setActiveThreadId(null)
    }
  }

  const selectThread = (threadId: string) => {
    setActiveThreadId(threadId)
  }

  const updateThreadTitle = (threadId: string, title: string) => {
    setThreads((prev) =>
      prev.map((t) => (t.id === threadId ? { ...t, title } : t)),
    )
  }

  const activeThread = threads.find((t) => t.id === activeThreadId) ?? null

  return {
    threads,
    activeThread,
    activeThreadId,
    loading,
    createThread,
    deleteThread,
    selectThread,
    updateThreadTitle,
    fetchThreads,
  }
}
