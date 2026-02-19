import { Loader2, Trash2, FileText, CheckCircle, XCircle, Clock, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { Document } from "@/types"

interface DocumentListProps {
  documents: Document[]
  onDelete: (id: string) => void
  currentUserId: string
}

function StatusBadge({ status, errorMessage }: { status: Document["status"]; errorMessage?: string | null }) {
  switch (status) {
    case "pending":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
          <Clock className="h-3 w-3" />
          Pending
        </span>
      )
    case "processing":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
          <Loader2 className="h-3 w-3 animate-spin" />
          Processing
        </span>
      )
    case "completed":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900/30 dark:text-green-400">
          <CheckCircle className="h-3 w-3" />
          Completed
        </span>
      )
    case "failed":
      return (
        <span
          className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800 dark:bg-red-900/30 dark:text-red-400"
          title={errorMessage || "Processing failed"}
        >
          <XCircle className="h-3 w-3" />
          Failed
        </span>
      )
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function DocumentList({ documents, onDelete, currentUserId }: DocumentListProps) {
  if (documents.length === 0) return null

  return (
    <div className="space-y-2">
      {documents.map((doc) => {
        const isOwner = doc.user_id === currentUserId

        return (
          <div
            key={doc.id}
            className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50"
          >
            <FileText className="h-5 w-5 shrink-0 text-muted-foreground" />

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="truncate text-sm font-medium">{doc.filename}</p>
                {doc.is_shared && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                    <Globe className="h-3 w-3" />
                    Shared
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{formatFileSize(doc.file_size)}</span>
                <span>·</span>
                {doc.status === "completed" && (
                  <>
                    <span>{doc.chunk_count} chunks</span>
                    <span>·</span>
                  </>
                )}
                <span>{formatDate(doc.created_at)}</span>
              </div>
              {doc.status === "failed" && doc.error_message && (
                <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                  {doc.error_message}
                </p>
              )}
            </div>

            <StatusBadge status={doc.status} errorMessage={doc.error_message} />

            {isOwner && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(doc.id)}
                className="h-8 w-8 shrink-0 p-0 text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      })}
    </div>
  )
}
