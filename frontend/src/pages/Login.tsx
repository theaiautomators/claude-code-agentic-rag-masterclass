import { useState } from 'react'
import { supabase } from '../lib/supabase'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export function Login() {
  const { session } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  if (session) {
    return <Navigate to="/" replace />
  }

  const handleAuth = async (isSignUp: boolean) => {
    if (!email || !password) {
      setError('Please enter both email and password')
      return
    }
    try {
      setLoading(true)
      setError(null)
      
      const { error } = isSignUp 
        ? await supabase.auth.signUp({ email, password })
        : await supabase.auth.signInWithPassword({ email, password })
        
      if (error) throw error
    } catch (err: any) {
      setError(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen w-full items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">RAG Masterclass</CardTitle>
          <CardDescription>Enter your email to sign in or create an account.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Input
                id="email"
                type="email"
                placeholder="m@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Input
                id="password"
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            
            {error && <div className="text-sm text-red-500 font-medium">{error}</div>}
            
            <div className="grid gap-2 pt-2">
              <Button disabled={loading} onClick={() => handleAuth(false)}>
                Sign In
              </Button>
              <Button disabled={loading} variant="outline" onClick={() => handleAuth(true)}>
                Create Account
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
