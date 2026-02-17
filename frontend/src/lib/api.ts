import { supabase } from "./supabase"

const API_BASE = import.meta.env.VITE_API_BASE_URL

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const headers = await getAuthHeaders()
  const res = await fetch(`${API_BASE}${path}`, { headers })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const headers = await getAuthHeaders()
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function apiDelete(path: string): Promise<void> {
  const headers = await getAuthHeaders()
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers,
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
}

export async function apiStreamPost(
  path: string,
  body: unknown,
  onDelta: (text: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
): Promise<void> {
  const headers = await getAuthHeaders()
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    onError(`API error: ${res.status}`)
    return
  }

  const reader = res.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    onError("No response body")
    return
  }

  let currentEvent = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    const lines = chunk.split("\n")

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith("data: ")) {
        const rawData = line.slice(6)
        try {
          const data = JSON.parse(rawData)
          if (currentEvent === "text_delta" && data.content) {
            onDelta(data.content)
          } else if (currentEvent === "done") {
            onDone()
          } else if (currentEvent === "error") {
            onError(data.message || "Stream error")
          }
        } catch {
          // Skip non-JSON data lines
        }
      }
    }
  }

  // If stream ended without a done event, still signal done
  onDone()
}
