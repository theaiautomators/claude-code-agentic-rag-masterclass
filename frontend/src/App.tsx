import { useAuth } from "@/hooks/useAuth"
import { AuthPage } from "@/components/auth/AuthPage"
import { ChatLayout } from "@/components/chat/ChatLayout"

function App() {
  const { session, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  if (!session) {
    return <AuthPage />
  }

  return <ChatLayout />
}

export default App
