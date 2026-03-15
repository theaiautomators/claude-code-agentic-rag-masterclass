import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { Login } from './pages/Login'
import { Chat } from './pages/Chat'

import { Ingest } from './pages/Ingest'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { session, loading } = useAuth()
  
  if (loading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>
  }
  
  if (!session) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/ingest" 
        element={
          <ProtectedRoute>
            <Ingest />
          </ProtectedRoute>
        } 
      />
    </Routes>
  )
}

export default App
