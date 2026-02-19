import { useState, useRef, type DragEvent, type ChangeEvent } from "react"
import { Upload, Loader2 } from "lucide-react"

interface FileDropZoneProps {
  onUpload: (file: File) => Promise<void>
  uploading: boolean
}

const ALLOWED_TYPES = ["text/plain", "text/markdown", "text/csv"]
const MAX_SIZE = 10 * 1024 * 1024 // 10MB

export function FileDropZone({ onUpload, uploading }: FileDropZoneProps) {
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      // Some browsers don't set MIME for .md files — check extension too
      const ext = file.name.split(".").pop()?.toLowerCase()
      if (!["txt", "md", "csv"].includes(ext || "")) {
        alert(`Unsupported file type. Allowed: .txt, .md, .csv`)
        return
      }
    }
    if (file.size > MAX_SIZE) {
      alert(`File too large. Maximum size: 10MB`)
      return
    }
    await onUpload(file)
  }

  const handleDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    // Reset input so the same file can be uploaded again
    e.target.value = ""
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => fileInputRef.current?.click()}
      className={`
        cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors
        ${dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-muted-foreground/50"}
        ${uploading ? "pointer-events-none opacity-60" : ""}
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.md,.csv"
        onChange={handleInputChange}
        className="hidden"
      />

      {uploading ? (
        <>
          <Loader2 className="mx-auto mb-3 h-10 w-10 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Uploading...</p>
        </>
      ) : (
        <>
          <Upload className="mx-auto mb-3 h-10 w-10 text-muted-foreground" />
          <p className="text-sm font-medium">
            Drop a file here or click to browse
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Supports .txt, .md, .csv — Max 10MB
          </p>
        </>
      )}
    </div>
  )
}
