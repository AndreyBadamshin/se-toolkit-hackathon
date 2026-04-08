import { useState, useEffect, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

interface Bookmark {
  id: number
  url: string
  title: string
  summary: string
  categories: string[]
  image_url: string | null
  created_at: string
}

interface Collection {
  id: number
  name: string
  color: string
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
  const [collections, setCollections] = useState<Collection[]>([])
  const [newUrl, setNewUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [filterCollection, setFilterCollection] = useState<number | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [editingBookmarkId, setEditingBookmarkId] = useState<number | null>(null)
  const [newCategoryInput, setNewCategoryInput] = useState('')
  const [showCollections, setShowCollections] = useState(false)
  const [newCollectionName, setNewCollectionName] = useState('')
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetchBookmarks()
    fetchCollections()
  }, [])

  const fetchBookmarks = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/api/bookmarks`, getAuthHeaders())
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

  const fetchCollections = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/collections`, getAuthHeaders())
      setCollections(response.data)
    } catch {
      // Silently fail - collections are optional
    }
  }

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) {
      fetchBookmarks()
      return
    }
    
    setLoading(true)
    try {
      const response = await axios.get(
        `${API_URL}/api/search?q=${encodeURIComponent(searchQuery)}`,
        getAuthHeaders()
      )
      setBookmarks(response.data)
    } catch {
      setError('Search failed')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCollection = async () => {
    if (!newCollectionName.trim()) return
    
    try {
      await axios.post(
        `${API_URL}/api/collections`,
        { name: newCollectionName.trim(), color: '#007bff' },
        getAuthHeaders()
      )
      setNewCollectionName('')
      await fetchCollections()
    } catch {
      setError('Failed to create collection')
    }
  }

  const handleAddToCollection = async (bookmarkId: number, collectionId: number) => {
    try {
      await axios.post(
        `${API_URL}/api/collections/${collectionId}/bookmarks/${bookmarkId}`,
        {},
        getAuthHeaders()
      )
    } catch {
      setError('Failed to add bookmark to collection')
    }
  }

  const handleExportJSON = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/import-export/export/json`, getAuthHeaders())
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'bookmarks.json'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Export failed')
    }
  }

  const handleExportCSV = () => {
    window.open(`${API_URL}/api/import-export/export/csv`, '_blank')
  }

  const handleImportCSV = async () => {
    if (!importFile) return
    
    const formData = new FormData()
    formData.append('file', importFile)
    
    try {
      await axios.post(`${API_URL}/api/import-export/import/csv`, formData, {
        ...getAuthHeaders(),
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setImportFile(null)
      await fetchBookmarks()
    } catch {
      setError('Import failed')
    }
  }

  const handleAddBookmark = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)

    try {
      await axios.post(`${API_URL}/api/bookmarks`, { url: newUrl }, getAuthHeaders())
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
      await axios.delete(`${API_URL}/api/bookmarks/${id}`, getAuthHeaders())
      setBookmarks(bookmarks.filter((b) => b.id !== id))
    } catch {
      setError('Failed to delete bookmark')
    }
  }

  const handleRemoveCategory = async (bookmarkId: number, category: string) => {
    try {
      const response = await axios.delete(
        `${API_URL}/api/bookmarks/${bookmarkId}/categories/${encodeURIComponent(category)}`,
        getAuthHeaders()
      )
      setBookmarks(bookmarks.map((b) => b.id === bookmarkId ? response.data : b))
    } catch {
      setError('Failed to remove category')
    }
  }

  const handleAddCategory = async (bookmarkId: number) => {
    if (!newCategoryInput.trim()) return
    
    try {
      const response = await axios.post(
        `${API_URL}/api/bookmarks/${bookmarkId}/categories`,
        { category: newCategoryInput.trim() },
        getAuthHeaders()
      )
      setBookmarks(bookmarks.map((b) => b.id === bookmarkId ? response.data : b))
      setNewCategoryInput('')
      setEditingBookmarkId(null)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to add category')
      } else {
        setError('Failed to add category')
      }
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  const allCategories = Array.from(new Set(bookmarks.flatMap((b) => b.categories || [])))
  const filteredBookmarks = filterCategory
    ? bookmarks.filter((b) => (b.categories || []).includes(filterCategory))
    : bookmarks
  
  const displayBookmarks = filterCollection
    ? filteredBookmarks // Will be filtered by collection when we fetch collection bookmarks
    : filteredBookmarks

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

        {/* Search Bar */}
        <div className="card shadow mb-4">
          <div className="card-body">
            <form onSubmit={handleSearch}>
              <div className="input-group">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search bookmarks with natural language..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button type="submit" className="btn btn-success">
                  Search
                </button>
                {searchQuery && (
                  <button 
                    type="button" 
                    className="btn btn-outline-secondary"
                    onClick={() => { setSearchQuery(''); fetchBookmarks(); }}
                  >
                    Clear
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>

        {/* Add Bookmark Form */}
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

        {allCategories.length > 0 && (
          <div className="mb-3 d-flex align-items-center gap-2 flex-wrap">
            <span className="text-muted">Filter by category:</span>
            <button
              className={`btn btn-sm ${!filterCategory ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => setFilterCategory('')}
            >
              All
            </button>
            {allCategories.map((cat) => (
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

        {/* Collections & Export/Import */}
        <div className="mb-3 d-flex gap-2 flex-wrap">
          <button
            className={`btn btn-sm ${showCollections ? 'btn-primary' : 'btn-outline-secondary'}`}
            onClick={() => setShowCollections(!showCollections)}
          >
            📁 Collections
          </button>
          <div className="dropdown">
            <button
              className="btn btn-sm btn-outline-secondary dropdown-toggle"
              type="button"
              onClick={() => setShowExportMenu(!showExportMenu)}
            >
              📥 Export/Import
            </button>
            {showExportMenu && (
              <div className="dropdown-menu show" style={{ display: 'block' }}>
                <button className="dropdown-item" onClick={handleExportJSON}>Export as JSON</button>
                <button className="dropdown-item" onClick={handleExportCSV}>Export as CSV</button>
                <div className="dropdown-divider"></div>
                <div className="px-3 py-2">
                  <input
                    type="file"
                    className="form-control form-control-sm"
                    accept=".csv"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  />
                  <button
                    className="btn btn-sm btn-primary mt-2 w-100"
                    onClick={handleImportCSV}
                    disabled={!importFile}
                  >
                    Import CSV
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {showCollections && (
          <div className="card shadow mb-4">
            <div className="card-body">
              <h6 className="mb-3">Collections</h6>
              <div className="d-flex gap-2 mb-3 flex-wrap">
                {collections.map((col) => (
                  <button
                    key={col.id}
                    className="btn btn-sm btn-outline-primary"
                    style={{ borderColor: col.color, color: col.color }}
                    onClick={() => setFilterCollection(filterCollection === col.id ? null : col.id)}
                  >
                    {col.name}
                  </button>
                ))}
              </div>
              <div className="input-group">
                <input
                  type="text"
                  className="form-control"
                  placeholder="New collection name..."
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateCollection()}
                />
                <button className="btn btn-sm btn-success" onClick={handleCreateCollection}>
                  Create
                </button>
              </div>
            </div>
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
                      <div className="d-flex flex-wrap gap-1 align-items-center">
                        {(bookmark.categories || []).map((cat) => (
                          <span 
                            key={cat} 
                            className={`badge ${CATEGORY_COLORS[cat.toLowerCase()] || 'bg-secondary'} category-badge d-inline-flex align-items-center`}
                          >
                            {cat}
                            <button
                              className="btn btn-sm text-white ms-1 p-0 border-0 bg-transparent"
                              onClick={() => handleRemoveCategory(bookmark.id, cat)}
                              style={{ lineHeight: 1, fontSize: '0.9rem' }}
                            >
                              ×
                            </button>
                          </span>
                        ))}
                        {(bookmark.categories || []).length < 5 && (
                          editingBookmarkId === bookmark.id ? (
                            <div className="d-inline-flex align-items-center gap-1">
                              <input
                                type="text"
                                className="form-control form-control-sm"
                                style={{ width: '120px', height: 'auto', padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                                value={newCategoryInput}
                                onChange={(e) => setNewCategoryInput(e.target.value)}
                                placeholder="New category"
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') {
                                    e.preventDefault()
                                    handleAddCategory(bookmark.id)
                                  } else if (e.key === 'Escape') {
                                    setEditingBookmarkId(null)
                                    setNewCategoryInput('')
                                  }
                                }}
                                autoFocus
                              />
                              <button
                                className="btn btn-sm btn-success"
                                style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                                onClick={() => handleAddCategory(bookmark.id)}
                              >
                                ✓
                              </button>
                              <button
                                className="btn btn-sm btn-secondary"
                                style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                                onClick={() => {
                                  setEditingBookmarkId(null)
                                  setNewCategoryInput('')
                                }}
                              >
                                ×
                              </button>
                            </div>
                          ) : (
                            <button
                              className="btn btn-sm btn-outline-secondary"
                              style={{ padding: '0.25rem 0.5rem', fontSize: '1rem', lineHeight: 1 }}
                              onClick={() => setEditingBookmarkId(bookmark.id)}
                            >
                              +
                            </button>
                          )
                        )}
                      </div>
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
                    
                    {/* Collection Assignment */}
                    {collections.length > 0 && (
                      <div className="mb-2">
                        <select
                          className="form-select form-select-sm"
                          style={{ fontSize: '0.8rem' }}
                          onChange={(e) => {
                            if (e.target.value) {
                              handleAddToCollection(bookmark.id, parseInt(e.target.value))
                              e.target.value = ''
                            }
                          }}
                          defaultValue=""
                        >
                          <option value="" disabled>Add to collection...</option>
                          {collections.map((col) => (
                            <option key={col.id} value={col.id}>{col.name}</option>
                          ))}
                        </select>
                      </div>
                    )}
                    
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
