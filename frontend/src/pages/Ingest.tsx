import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Trash2, FileUp, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

type Doc = {
  id: string
  filename: string
  status: string
  chunk_count: number
  created_at: string
}

export function Ingest() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [docs, setDocs] = useState<Doc[]>([])
  const [uploading, setUploading] = useState(false)

  const getAuthHeaders = () => ({
    'Authorization': `Bearer ${session?.access_token}`
  })

  useEffect(() => {
    fetchDocs()
    // We could set up Realtime here, but for simplicity we'll just poll every 3s if any is processing
    const interval = setInterval(() => {
      setDocs(currentDocs => {
        if (currentDocs.some(d => d.status === 'processing')) {
          fetchDocs()
        }
        return currentDocs
      })
    }, 3000)
    return () => clearInterval(interval)
  }, [session])

  const fetchDocs = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/documents', { headers: getAuthHeaders() })
      if (!res.ok) return
      setDocs(await res.json())
    } catch(e) {}
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return
    const file = e.target.files[0]
    
    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      await fetch('http://127.0.0.1:8000/ingest', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        },
        body: formData
      })
      fetchDocs()
    } catch(e) {
      console.error(e)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await fetch(`http://127.0.0.1:8000/documents/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      fetchDocs()
    } catch(e) {}
  }

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" onClick={() => navigate('/')}>
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Chat
        </Button>
        <h1 className="text-3xl font-bold">Knowledge Base Ingestion</h1>
      </div>

      <div className="grid gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Upload Document</CardTitle>
            <CardDescription>Upload PDFs, TXT, or MD files to be chunked and embedded by Ollama.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center w-full">
              <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer bg-muted hover:bg-muted/80">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <FileUp className="w-10 h-10 mb-3 text-muted-foreground" />
                  <p className="mb-2 text-sm text-muted-foreground">
                    <span className="font-semibold">{uploading ? 'Uploading and chunking...' : 'Click to upload'}</span>
                  </p>
                </div>
                <input type="file" className="hidden" onChange={handleUpload} disabled={uploading} />
              </label>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Indexed Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {docs.map(doc => (
                <div key={doc.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">{doc.filename}</p>
                    <div className="flex text-sm text-muted-foreground gap-4">
                      <span>Status: <span className={doc.status === 'completed' ? 'text-green-500' : 'text-yellow-500'}>{doc.status}</span></span>
                      <span>Chunks: {doc.chunk_count || 0}</span>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10 hover:text-destructive" onClick={() => handleDelete(doc.id)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
              {docs.length === 0 && <p className="text-sm text-muted-foreground text-center py-4">No documents indexed yet.</p>}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
