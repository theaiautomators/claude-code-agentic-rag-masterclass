import { useDocuments } from "@/hooks/useDocuments"
import { useAuth } from "@/hooks/useAuth"
import { FileDropZone } from "./FileDropZone"
import { DocumentList } from "./DocumentList"
import { FileText } from "lucide-react"

export function DocumentsPage() {
  const { documents, loading, uploading, error, uploadDocument, deleteDocument } =
    useDocuments()
  const { user } = useAuth()
  const currentUserId = user?.id ?? ""

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="mx-auto w-full max-w-3xl flex-1 overflow-y-auto p-6">
        <h1 className="mb-6 text-2xl font-bold">Documents</h1>

        {/* Upload zone */}
        <div className="mb-6">
          <FileDropZone onUpload={uploadDocument} uploading={uploading} />
          {error && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
        </div>

        {/* Document list */}
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading documents...</p>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText className="mb-3 h-12 w-12 text-muted-foreground/50" />
            <p className="text-sm font-medium text-muted-foreground">
              No documents yet
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Upload a text file to get started with RAG
            </p>
          </div>
        ) : (
          <DocumentList documents={documents} onDelete={deleteDocument} currentUserId={currentUserId} />
        )}
      </div>
    </div>
  )
}
