import { useState, useEffect, useCallback } from "react"
import { apiGet, apiUploadFile, apiDelete } from "@/lib/api"
import { supabase } from "@/lib/supabase"
import type { Document } from "@/types"

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await apiGet<{ documents: Document[] }>("/documents/")
      setDocuments(data.documents)
    } catch (err) {
      console.error("Failed to fetch documents:", err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  // Subscribe to Supabase Realtime for document status updates
  useEffect(() => {
    const channel = supabase
      .channel("documents-status")
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "documents",
        },
        (payload) => {
          const updated = payload.new as Document
          setDocuments((prev) =>
            prev.map((doc) =>
              doc.id === updated.id ? { ...doc, ...updated } : doc,
            ),
          )
        },
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  // Polling fallback: when any doc is pending/processing, poll every 2s
  useEffect(() => {
    const hasPending = documents.some(
      (d) => d.status === "pending" || d.status === "processing",
    )
    if (!hasPending) return

    const interval = setInterval(() => {
      fetchDocuments()
    }, 2000)

    return () => clearInterval(interval)
  }, [documents, fetchDocuments])

  const uploadDocument = async (file: File) => {
    setUploading(true)
    setError(null)
    try {
      const doc = await apiUploadFile<Document>("/documents/upload", file)
      setDocuments((prev) => [doc, ...prev])
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed"
      setError(message)
      throw err
    } finally {
      setUploading(false)
    }
  }

  const deleteDocument = async (id: string) => {
    try {
      await apiDelete(`/documents/${id}`)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      console.error("Failed to delete document:", err)
    }
  }

  return {
    documents,
    loading,
    uploading,
    error,
    uploadDocument,
    deleteDocument,
    fetchDocuments,
  }
}
