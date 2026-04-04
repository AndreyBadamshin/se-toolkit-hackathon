import { useState, useEffect, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

// In production (nginx), API is proxied to /auth, /bookmarks, /health
// In development (Vite dev server), proxy is configured in vite.config.ts
// So we use empty string (relative URLs) by default
const API_URL = import.meta.env.VITE_API_URL || ''

interface Bookmark {
  id: number
  url: string
  title: string
  summary: string
  tags: string[]
  category: string
  image_url: string | null
  created_at: string
}

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return { headers: { Authorization: `Bearer ${token}` } }
}

const CATEGORY_COLORS: Record<string, string> = {
  tech: 'bg-primary',
  science: 'bg-success',
  education: 'bg-info',
  entertainment: 'bg-warning',
  news: 'bg-danger',
  business: 'bg-secondary',
  health: 'bg-success',
  sports: 'bg-danger',
  other: 'bg-light text-dark',
}

export default function BookmarkList() {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([])
  const [newUrl, setNewUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [filterCategory, setFilterCategory] = useState<string>('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchBookmarks()
  }, [])

  const fetchBookmarks = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/bookmarks`, getAuthHeaders())
      setBookmarks(response.data)
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        localStorage.removeItem('token')
        navigate('/login')
        return
      }
      setError('Failed to load bookmarks')
    } finally {
      setLoading(false)
    }
  }

  const handleAddBookmark = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      await axios.post(`${API_URL}/bookmarks`, { url: newUrl }, getAuthHeaders())
      setNewUrl('')
      await fetchBookmarks()
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to save bookmark')
      } else {
        setError('Failed to save bookmark')
      }
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteBookmark = async (id: number) => {
    try {
      await axios.delete(`${API_URL}/bookmarks/${id}`, getAuthHeaders())
      setBookmarks(bookmarks.filter((b) => b.id !== id))
    } catch {
      setError('Failed to delete bookmark')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  const categories = Array.from(new Set(bookmarks.map((b) => b.category)))
  const filteredBookmarks = filterCategory
    ? bookmarks.filter((b) => b.category === filterCategory)
    : bookmarks

  return (
    <div className="container-fluid">
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
        <div className="container">
          <a className="navbar-brand" href="#">Smart Bookmark Manager</a>
          <button className="btn btn-outline-light" onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <div className="container">
        {error && (
          <div className="alert alert-danger alert-dismissible fade show" role="alert">
            {error}
            <button type="button" className="btn-close" onClick={() => setError('')}></button>
          </div>
        )}

        <div className="card shadow mb-4">
          <div className="card-body">
            <form onSubmit={handleAddBookmark}>
              <div className="input-group">
                <input
                  type="url"
                  className="form-control"
                  placeholder="Enter URL to save..."
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  required
                />
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                      Analyzing...
                    </>
                  ) : (
                    'Save Bookmark'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>

        {categories.length > 0 && (
          <div className="mb-3 d-flex align-items-center gap-2 flex-wrap">
            <span className="text-muted">Filter by category:</span>
            <button
              className={`btn btn-sm ${!filterCategory ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => setFilterCategory('')}
            >
              All
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                className={`btn btn-sm ${filterCategory === cat ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setFilterCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        )}

        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border loading-spinner text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : filteredBookmarks.length === 0 ? (
          <div className="text-center py-5 text-muted">
            <h4>No bookmarks yet</h4>
            <p>Add your first bookmark above!</p>
          </div>
        ) : (
          <div className="row g-4">
            {filteredBookmarks.map((bookmark) => (
              <div key={bookmark.id} className="col-md-6 col-lg-4">
                <div className="card bookmark-card h-100">
                  {bookmark.image_url && (
                    <img
                      src={bookmark.image_url}
                      className="card-img-top"
                      alt=""
                      style={{ height: '150px', objectFit: 'cover' }}
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                    />
                  )}
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-start mb-2">
                      <span className={`badge ${CATEGORY_COLORS[bookmark.category] || 'bg-secondary'} category-badge`}>
                        {bookmark.category}
                      </span>
                      <button
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => handleDeleteBookmark(bookmark.id)}
                      >
                        &times;
                      </button>
                    </div>
                    <h5 className="card-title">
                      <a href={bookmark.url} target="_blank" rel="noopener noreferrer" className="text-decoration-none">
                        {bookmark.title}
                      </a>
                    </h5>
                    <p className="card-text text-muted small">{bookmark.summary}</p>
                    <div className="mb-2">
                      {bookmark.tags.map((tag, i) => (
                        <span key={i} className="badge bg-light text-dark tag-badge">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <small className="text-muted">
                      {new Date(bookmark.created_at).toLocaleDateString()}
                    </small>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
