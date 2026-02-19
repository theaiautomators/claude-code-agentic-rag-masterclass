import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ExternalLink, RefreshCw, Database, Server, Brain, Activity, LayoutDashboard } from "lucide-react"

interface ServiceStatus {
  name: string
  status: "connected" | "error" | "checking" | "disabled"
  detail?: string
  url?: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const LANGSMITH_URL = "https://smith.langchain.com"

const quickLinks = [
  {
    name: "Supabase Studio",
    description: "Database, Auth, Storage dashboard",
    url: "http://localhost:54323",
    icon: Database,
    color: "text-emerald-500",
  },
  {
    name: "Backend API Docs",
    description: "FastAPI Swagger UI",
    url: "http://localhost:8001/docs",
    icon: Server,
    color: "text-blue-500",
  },
  {
    name: "LangSmith",
    description: "LLM traces & observability",
    url: LANGSMITH_URL,
    icon: Activity,
    color: "text-amber-500",
  },
  {
    name: "OpenAI Platform",
    description: "API keys, usage & billing",
    url: "https://platform.openai.com",
    icon: Brain,
    color: "text-violet-500",
  },
  {
    name: "Supabase API",
    description: "PostgREST endpoint",
    url: "http://localhost:54321",
    icon: LayoutDashboard,
    color: "text-teal-500",
  },
]

export function DebugPage() {
  const [services, setServices] = useState<ServiceStatus[]>([])
  const [loading, setLoading] = useState(false)

  const checkServices = async () => {
    setLoading(true)
    const results: ServiceStatus[] = []

    // Check Backend API
    try {
      const res = await fetch(`${API_BASE}/health`)
      if (res.ok) {
        results.push({ name: "Backend API", status: "connected", detail: API_BASE, url: "http://localhost:8001/docs" })
      } else {
        results.push({ name: "Backend API", status: "error", detail: `HTTP ${res.status}`, url: "http://localhost:8001/docs" })
      }
    } catch {
      results.push({ name: "Backend API", status: "error", detail: "Unreachable" })
    }

    // Check Supabase
    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/`, {
        headers: { apikey: import.meta.env.VITE_SUPABASE_ANON_KEY || "" },
      })
      if (res.ok || res.status === 200) {
        results.push({ name: "Supabase", status: "connected", detail: SUPABASE_URL, url: "http://localhost:54323" })
      } else {
        results.push({ name: "Supabase", status: "error", detail: `HTTP ${res.status}`, url: "http://localhost:54323" })
      }
    } catch {
      results.push({ name: "Supabase", status: "error", detail: "Unreachable" })
    }

    // Check service health (OpenAI + LangSmith via backend)
    try {
      const res = await fetch(`${API_BASE}/health/services`)
      if (res.ok) {
        const data = await res.json()
        results.push({
          name: "OpenAI",
          status: data.openai?.configured ? "connected" : "error",
          detail: data.openai?.configured ? "API key configured" : "API key missing",
          url: "https://platform.openai.com",
        })
        results.push({
          name: "LangSmith",
          status: data.langsmith?.enabled ? "connected" : "disabled",
          detail: data.langsmith?.enabled
            ? `Project: ${data.langsmith.project}`
            : "Tracing disabled",
          url: LANGSMITH_URL,
        })
      } else {
        results.push({ name: "OpenAI", status: "error", detail: "Could not check", url: "https://platform.openai.com" })
        results.push({ name: "LangSmith", status: "error", detail: "Could not check", url: LANGSMITH_URL })
      }
    } catch {
      results.push({ name: "OpenAI", status: "error", detail: "Backend unreachable", url: "https://platform.openai.com" })
      results.push({ name: "LangSmith", status: "error", detail: "Backend unreachable", url: LANGSMITH_URL })
    }

    setServices(results)
    setLoading(false)
  }

  useEffect(() => {
    checkServices()
  }, [])

  const statusDot = (status: ServiceStatus["status"]) => {
    const colors = {
      connected: "bg-emerald-500",
      error: "bg-red-500",
      checking: "bg-yellow-500 animate-pulse",
      disabled: "bg-muted-foreground/50",
    }
    return (
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${colors[status]}`} />
    )
  }

  const statusLabel = (status: ServiceStatus["status"]) => {
    const labels = {
      connected: "Connected",
      error: "Error",
      checking: "Checking...",
      disabled: "Disabled",
    }
    return labels[status]
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">Debug</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Service health and diagnostics
      </p>

      {/* Quick Links */}
      <div className="mt-8">
        <h2 className="text-lg font-medium">Quick Links</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Open your tools and dashboards
        </p>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {quickLinks.map((link) => (
            <a
              key={link.name}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group"
            >
              <Card className="h-full transition-colors hover:bg-accent/50">
                <CardContent className="flex flex-col gap-2 p-4">
                  <div className="flex items-center justify-between">
                    <link.icon className={`h-5 w-5 ${link.color}`} />
                    <ExternalLink className="h-3.5 w-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{link.name}</p>
                    <p className="text-xs text-muted-foreground">{link.description}</p>
                  </div>
                </CardContent>
              </Card>
            </a>
          ))}
        </div>
      </div>

      {/* Services */}
      <div className="mt-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Services</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={checkServices}
            disabled={loading}
          >
            <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        <Card className="mt-3">
          <CardContent className="p-0">
            <div className="divide-y">
              {services.length === 0 && (
                <div className="px-4 py-3 text-sm text-muted-foreground">
                  Checking services...
                </div>
              )}
              {services.map((service) => {
                const row = (
                  <div className={`flex items-center justify-between px-4 py-3 ${service.url ? "hover:bg-accent/50 transition-colors" : ""}`}>
                    <div className="flex items-center gap-3">
                      {statusDot(service.status)}
                      <span className="text-sm font-medium">{service.name}</span>
                      {service.url && (
                        <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {service.detail && (
                        <span className="text-xs text-muted-foreground">
                          {service.detail}
                        </span>
                      )}
                      <span className="text-xs font-medium">
                        {statusLabel(service.status)}
                      </span>
                    </div>
                  </div>
                )

                return service.url ? (
                  <a
                    key={service.name}
                    href={service.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group block"
                  >
                    {row}
                  </a>
                ) : (
                  <div key={service.name}>{row}</div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Environment Info */}
      <div className="mt-6">
        <h2 className="text-lg font-medium">Environment</h2>
        <Card className="mt-3">
          <CardContent className="p-0">
            <div className="divide-y text-sm">
              <div className="flex justify-between px-4 py-2.5">
                <span className="text-muted-foreground">API Base</span>
                <code className="text-xs">{API_BASE}</code>
              </div>
              <div className="flex justify-between px-4 py-2.5">
                <span className="text-muted-foreground">Supabase URL</span>
                <code className="text-xs">{SUPABASE_URL}</code>
              </div>
              <div className="flex justify-between px-4 py-2.5">
                <span className="text-muted-foreground">Frontend Port</span>
                <code className="text-xs">5173</code>
              </div>
              <div className="flex justify-between px-4 py-2.5">
                <span className="text-muted-foreground">Backend Port</span>
                <code className="text-xs">8001</code>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
