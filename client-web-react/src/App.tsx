import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './Login'
import Register from './Register'
import BookmarkList from './BookmarkList'

function getToken(): string | null {
  return localStorage.getItem('token')
}

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const token = getToken()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    setIsAuthenticated(!!getToken())
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={<Login onAuthSuccess={() => setIsAuthenticated(true)} />}
        />
        <Route
          path="/register"
          element={<Register onAuthSuccess={() => setIsAuthenticated(true)} />}
        />
        <Route
          path="/bookmarks"
          element={
            <ProtectedRoute>
              <BookmarkList />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/bookmarks" replace />} />
        <Route path="*" element={<Navigate to="/bookmarks" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
