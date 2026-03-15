import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { ScrollArea } from '../components/ui/scroll-area'
import { MessageSquare, Plus, Send, LogOut, FileText, Database } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

type Thread = {
  id: string
  title: string
  created_at: string
}

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export function Chat() {
  const { session, user, signOut } = useAuth()
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  // Fetch threads only when we have a valid session
  useEffect(() => {
    if (session?.access_token) {
      fetchThreads()
    }
  }, [session])

  useEffect(() => {
    if (activeThreadId) {
      fetchMessages(activeThreadId)
    } else {
      setMessages([])
    }
  }, [activeThreadId])

  // Auto scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const getAuthHeaders = (): Record<string, string> => {
    if (!session?.access_token) return {}
    return {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    }
  }

  const fetchThreads = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/threads', { headers: getAuthHeaders() })
      if (!res.ok) return
      const data = await res.json()
      setThreads(data)
      if (data.length > 0 && !activeThreadId) {
        setActiveThreadId(data[0].id)
      }
    } catch (e) {
      console.error(e)
    }
  }

  const fetchMessages = async (threadId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/threads/${threadId}/messages`, { headers: getAuthHeaders() })
      if (!res.ok) return
      const data = await res.json()
      setMessages(data)
    } catch (e) {
      console.error(e)
    }
  }

  const createNewThread = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/threads', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ title: 'New Conversation' })
      })
      if (!res.ok) return
      const newThread = await res.json()
      setThreads([newThread, ...threads])
      setActiveThreadId(newThread.id)
    } catch (e) {
      console.error(e)
    }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || !activeThreadId || isStreaming) return

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: inputValue }
    setMessages(prev => [...prev, userMsg])
    setInputValue('')
    setIsStreaming(true)

    // Add empty assistant message placeholder for streaming
    const assistantMsgId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, { id: assistantMsgId, role: 'assistant', content: '' }])

    try {
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          thread_id: activeThreadId,
          message: userMsg.content
        })
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }))
        throw new Error(err.detail ?? 'Request failed')
      }
      if (!res.body) throw new Error('No response body')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let done = false

      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        const chunkValue = decoder.decode(value)
        
        // chunkValue could contain multiple "data: {...}\n\n"
        const lines = chunkValue.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim()
            if (dataStr === '[DONE]') {
              break
            }
            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr)
                setMessages(prev => 
                  prev.map(m => 
                    m.id === assistantMsgId ? { ...m, content: m.content + parsed.content } : m
                  )
                )
              } catch (e) {}
            }
          }
        }
      }
    } catch (e) {
      console.error(e)
      setMessages(prev => 
        prev.map(m => m.id === assistantMsgId ? { ...m, content: 'Error fetching response' } : m)
      )
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 border-r bg-muted/30 flex flex-col">
        <div className="p-4 border-b flex items-center justify-between">
          <span className="font-semibold text-sm">Ollama RAG</span>
          <div className="flex gap-2">
            <Button variant="ghost" size="icon" onClick={() => navigate('/ingest')} title="Knowledge Base">
              <Database className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => createNewThread()} title="New Chat">
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {threads.map(t => (
              <button
                key={t.id}
                onClick={() => setActiveThreadId(t.id)}
                className={`w-full flex items-center gap-2 px-2 py-2 text-sm rounded-md transition-colors ${activeThreadId === t.id ? 'bg-secondary font-medium' : 'hover:bg-muted text-muted-foreground'}`}
              >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <span className="truncate">{t.title}</span>
              </button>
            ))}
          </div>
        </ScrollArea>
        <div className="p-4 border-t flex items-center justify-between">
          <div className="text-xs truncate w-32 text-muted-foreground" title={user?.email}>
            {user?.email}
          </div>
          <Button variant="ghost" size="icon" onClick={signOut}>
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4" ref={scrollRef}>
          <div className="max-w-3xl mx-auto space-y-6 pb-20 mt-4">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 shrink-0 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
                    <FileText className="h-4 w-4" />
                  </div>
                )}
                <div className={`px-4 py-2 max-w-[80%] rounded-lg ${msg.role === 'user' ? 'bg-primary text-primary-foreground rounded-br-none' : 'bg-muted rounded-bl-none'}`}>
                  <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                </div>
              </div>
            ))}
            {messages.length === 0 && (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm py-20">
                Start a conversation...
              </div>
            )}
            {isStreaming && messages.length > 0 && messages[messages.length-1].content === '' && (
              <div className="flex items-center gap-2 text-muted-foreground text-sm ml-12">
                <span className="animate-pulse">Thinking...</span>
              </div>
            )}
          </div>
        </div>
        
        {/* Input Form */}
        <div className="p-4 bg-background">
          <form onSubmit={sendMessage} className="max-w-3xl mx-auto relative flex items-center">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Message Ollama RAG..."
              className="pr-12 py-6 rounded-xl shadow-sm border-muted-foreground/20"
              disabled={!activeThreadId || isStreaming}
            />
            <Button 
              type="submit" 
              size="icon" 
              className="absolute right-2 rounded-lg"
              disabled={!inputValue.trim() || !activeThreadId || isStreaming}
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
          <div className="text-center text-xs text-muted-foreground mt-3">
            Local Ollama embeddings + Qwen2.5:3b Generation
          </div>
        </div>
      </div>
    </div>
  )
}
