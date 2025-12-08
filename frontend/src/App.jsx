import React, { useState, useEffect } from 'react'
import axios from 'axios'
import LandingPage from './LandingPage'
import './App.css'

const API_BASE = '/api'

// Configure axios
axios.defaults.baseURL = API_BASE
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function App() {
  const [user, setUser] = useState(null)
  const [workspaces, setWorkspaces] = useState([])
  const [selectedWorkspace, setSelectedWorkspace] = useState(null)
  const [documents, setDocuments] = useState([])
  const [activeTab, setActiveTab] = useState('upload') // upload, search, chat, summarize

  useEffect(() => {
    checkAuth()
  }, [])

  useEffect(() => {
    if (user) {
      loadWorkspaces()
    }
  }, [user])

  useEffect(() => {
    if (selectedWorkspace) {
      loadDocuments()
    }
  }, [selectedWorkspace])

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        const response = await axios.get('/auth/users/me/')
        setUser(response.data)
      } catch (error) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
    }
  }

  const handleLogin = async (username, password) => {
    try {
      const response = await axios.post('/auth/token/', { username, password })
      localStorage.setItem('access_token', response.data.access)
      localStorage.setItem('refresh_token', response.data.refresh)
      await checkAuth()
    } catch (error) {
      throw new Error(error.response?.data?.detail || error.message || 'Login failed')
    }
  }

  const handleRegister = async (username, email, password, passwordConfirm) => {
    try {
      const response = await axios.post('/auth/users/register/', {
        username,
        email,
        password,
        password_confirm: passwordConfirm
      })
      // Auto-login after registration
      localStorage.setItem('access_token', response.data.access)
      localStorage.setItem('refresh_token', response.data.refresh)
      await checkAuth()
      // Create a default workspace for new user
      try {
        await axios.post('/auth/workspaces/', {
          name: 'My Workspace',
          description: 'Default workspace'
        })
        await loadWorkspaces()
      } catch (err) {
        console.error('Failed to create default workspace:', err)
      }
    } catch (error) {
      const errorMsg = error.response?.data
      if (typeof errorMsg === 'object') {
        const messages = Object.values(errorMsg).flat()
        throw new Error(messages.join(', ') || 'Registration failed')
      }
      throw new Error(error.response?.data?.detail || error.message || 'Registration failed')
    }
  }

  const loadWorkspaces = async () => {
    try {
      const response = await axios.get('/auth/workspaces/')
      setWorkspaces(response.data.results || response.data)
      if (response.data.results?.length > 0 || response.data?.length > 0) {
        setSelectedWorkspace(response.data.results?.[0] || response.data[0])
      }
    } catch (error) {
      console.error('Failed to load workspaces:', error)
    }
  }

  const loadDocuments = async () => {
    if (!selectedWorkspace) return
    try {
      const response = await axios.get('/api/documents/')
      setDocuments(response.data.results || response.data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    }
  }

  if (!user) {
    return <LandingPage onLoginClick={handleLogin} onRegisterClick={handleRegister} />
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <span className="header-icon">📚</span>
            <h1 className="header-title">PaperBot</h1>
          </div>
          <div className="header-right">
            <div className="user-info">
              <span className="user-greeting">Welcome,</span>
              <span className="user-name">{user.username}</span>
            </div>
            <button className="btn-logout" onClick={() => {
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              setUser(null)
            }}>
              Logout
            </button>
          </div>
        </div>
      </header>

      {workspaces.length > 0 && (
        <div className="workspace-selector">
          <label className="workspace-label">
            <span className="workspace-icon">📁</span>
            Workspace:
          </label>
          <select
            value={selectedWorkspace?.id || ''}
            onChange={(e) => {
              const ws = workspaces.find(w => w.id === parseInt(e.target.value))
              setSelectedWorkspace(ws)
            }}
            className="workspace-select"
          >
            {workspaces.map(ws => (
              <option key={ws.id} value={ws.id}>{ws.name}</option>
            ))}
          </select>
          {!selectedWorkspace && (
            <button 
              className="btn-create-workspace"
              onClick={async () => {
                try {
                  const response = await axios.post('/auth/workspaces/', {
                    name: 'New Workspace',
                    description: ''
                  })
                  await loadWorkspaces()
                  setSelectedWorkspace(response.data)
                } catch (error) {
                  alert('Failed to create workspace: ' + (error.response?.data?.error || error.message))
                }
              }}
            >
              + Create Workspace
            </button>
          )}
        </div>
      )}

      <div className="tabs">
        <button
          className={activeTab === 'upload' ? 'active' : ''}
          onClick={() => setActiveTab('upload')}
        >
          Upload
        </button>
        <button
          className={activeTab === 'search' ? 'active' : ''}
          onClick={() => setActiveTab('search')}
        >
          Search/Query
        </button>
        <button
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          Chat
        </button>
        <button
          className={activeTab === 'summarize' ? 'active' : ''}
          onClick={() => setActiveTab('summarize')}
        >
          Summarize
        </button>
      </div>

      <div className="content">
        {activeTab === 'upload' && (
          <DocumentUpload
            workspaceId={selectedWorkspace?.id}
            onUpload={loadDocuments}
          />
        )}
        {activeTab === 'search' && (
          <QueryInterface workspaceId={selectedWorkspace?.id} />
        )}
        {activeTab === 'chat' && (
          <ChatInterface workspaceId={selectedWorkspace?.id} />
        )}
        {activeTab === 'summarize' && (
          <SummarizeInterface
            workspaceId={selectedWorkspace?.id}
            documents={documents}
          />
        )}
      </div>

      <div className="documents-list">
        <h2>📄 Documents ({documents.length})</h2>
        {documents.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📄</div>
            <div className="empty-state-title">No documents uploaded yet</div>
            <div className="empty-state-description">Upload a PDF to get started with your research</div>
          </div>
        ) : (
          <ul>
            {documents.map(doc => {
              const statusColors = {
                'uploaded': '#64748b',
                'processing': '#f59e0b',
                'extracted': '#6366f1',
                'chunked': '#6366f1',
                'embedded': '#8b5cf6',
                'indexed': '#8b5cf6',
                'failed': '#ef4444'
              }
              const statusIcons = {
                'uploaded': '📤',
                'processing': '⏳',
                'extracted': '📝',
                'chunked': '✂️',
                'embedded': '🔢',
                'indexed': '✅',
                'failed': '❌'
              }
              return (
                <li key={doc.id}>
                  <div>
                    <strong>{doc.title}</strong>
                    <div style={{ marginTop: '6px', fontSize: '0.8125rem', color: '#64748b', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                      <span>{doc.filename}</span>
                      {doc.file_size && <span>•</span>}
                      {doc.file_size && <span>{(doc.file_size / 1024).toFixed(1)} KB</span>}
                    </div>
                  </div>
                  <span style={{
                    padding: '6px 14px',
                    borderRadius: '12px',
                    fontSize: '0.8125rem',
                    fontWeight: '600',
                    background: statusColors[doc.status] || '#64748b',
                    color: 'white',
                    textTransform: 'capitalize',
                    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                    letterSpacing: '0.3px'
                  }}>
                    {statusIcons[doc.status] || '📄'} {doc.status}
                  </span>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}

function LoginForm({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    await onLogin(username, password)
    setLoading(false)
  }

  return (
    <div className="login-container">
      <div className="card">
        <h2>🔬 PaperBot</h2>
        <p style={{ color: '#666', marginBottom: '24px' }}>Research Assistant Agent</p>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="input"
            required
            disabled={loading}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
            required
            disabled={loading}
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
          <p style={{ marginTop: '16px', fontSize: '12px', color: '#888', textAlign: 'center' }}>
            Default: admin / admin123
          </p>
        </form>
      </div>
    </div>
  )
}

function DocumentUpload({ workspaceId, onUpload }) {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !workspaceId) {
      setMessage('Please select a file and workspace')
      return
    }

    setUploading(true)
    setMessage('')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('workspace_id', workspaceId)
    if (title) formData.append('title', title)

    try {
      await axios.post('/api/documents/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setMessage('✅ Document uploaded! Processing in background...')
      setFile(null)
      setTitle('')
      setTimeout(() => {
        onUpload()
        setMessage('')
      }, 2000)
    } catch (error) {
      setMessage('❌ Upload failed: ' + (error.response?.data?.error || error.message))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="card">
      <h2>Upload PDF Document</h2>
      <p>Upload research papers and documents for intelligent analysis and retrieval</p>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">PDF File</label>
          <div className={`file-upload-area ${file ? 'has-file' : ''}`} onClick={() => document.getElementById('file-input')?.click()}>
            <input
              id="file-input"
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files[0])}
              className="file-input"
              required
              disabled={uploading}
            />
            <label htmlFor="file-input" className="file-label">
              Choose File
            </label>
            {file && (
              <div className="file-name">
                ✓ {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </div>
            )}
            {!file && (
              <div className="file-name" style={{ marginTop: '0.5rem' }}>
                No file selected
              </div>
            )}
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Document Title (optional)</label>
          <input
            type="text"
            placeholder="Enter a title for this document"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input"
            disabled={uploading}
          />
        </div>
        {message && (
          <div style={{
            padding: '0.75rem 1rem',
            marginBottom: '1.5rem',
            borderRadius: '8px',
            background: message.includes('✅') ? '#d1fae5' : '#fee2e2',
            color: message.includes('✅') ? '#065f46' : '#991b1b',
            border: `1px solid ${message.includes('✅') ? '#a7f3d0' : '#fecaca'}`,
            fontSize: '0.875rem',
            fontWeight: '500'
          }}>
            {message}
          </div>
        )}
        <button type="submit" className="btn btn-primary" disabled={uploading || !file}>
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </form>
    </div>
  )
}

function QueryInterface({ workspaceId }) {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query || !workspaceId) {
      setError('Please enter a question and select a workspace')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)
    try {
      const response = await axios.post('/api/query/', {
        workspace_id: workspaceId,
        query: query,
        top_k: 5
      })
      setResult(response.data)
    } catch (error) {
      setError('Query failed: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Ask a Question</h2>
      <p>Query your documents using natural language and get intelligent answers with citations</p>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Your Question</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., What is the main contribution of this paper? What methodology was used?"
            className="textarea"
            required
            disabled={loading}
            rows="5"
          />
        </div>
        {error && (
          <div style={{
            padding: '0.75rem 1rem',
            marginBottom: '1.5rem',
            borderRadius: '8px',
            background: '#fee2e2',
            color: '#991b1b',
            border: '1px solid #fecaca',
            fontSize: '0.875rem',
            fontWeight: '500'
          }}>
            {error}
          </div>
        )}
        <button type="submit" className="btn btn-primary" disabled={loading || !query}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {result && (
        <div className="result">
          <h3>💡 Answer:</h3>
          <p>{result.answer}</p>
          {result.citations && result.citations.length > 0 && (
            <div>
              <h4>📚 Citations ({result.citations.length}):</h4>
              <ul>
                {result.citations.map((cite, idx) => (
                  <li key={idx}>
                    <strong>{cite.document_title}</strong>
                    {cite.page_number && <span style={{ color: '#888', marginLeft: '8px' }}>Page {cite.page_number}</span>}
                    <br />
                    <small style={{ display: 'block', marginTop: '8px', color: '#666' }}>
                      {cite.snippet.substring(0, 150)}...
                    </small>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ChatInterface({ workspaceId }) {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (workspaceId && !sessionId) {
      createSession()
    }
  }, [workspaceId])

  const createSession = async () => {
    try {
      const response = await axios.post('/api/chat/', {
        workspace_id: workspaceId,
        title: 'New Chat'
      })
      setSessionId(response.data.id)
    } catch (error) {
      console.error('Failed to create session:', error)
      setError('Failed to create chat session')
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input || !sessionId) return

    const userMessage = { role: 'user', content: input }
    setMessages([...messages, userMessage])
    setInput('')
    setLoading(true)
    setError('')

    try {
      const response = await axios.post(`/api/chat/${sessionId}/message/`, {
        message: input,
        workspace_id: workspaceId
      })
      setMessages([...messages, userMessage, {
        role: 'assistant',
        content: response.data.answer,
        citations: response.data.citations
      }])
    } catch (error) {
      setError('Failed to send message: ' + (error.response?.data?.error || error.message))
      setMessages([...messages, userMessage]) // Keep user message even on error
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Chat</h2>
      <p>Have an interactive conversation with your documents and get contextual answers</p>
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state" style={{ padding: '3rem 2rem' }}>
            <div className="empty-state-icon">💬</div>
            <div className="empty-state-title">Start a conversation</div>
            <div className="empty-state-description">Ask a question about your documents to begin</div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <strong>{msg.role === 'user' ? 'You' : '🤖 Assistant'}:</strong>
              <p>{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="citations">
                  <strong>Sources:</strong> {msg.citations.map((cite, i) => (
                    <span key={i} style={{ marginLeft: '8px' }}>{cite.document_title}</span>
                  )).join(', ')}
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="message assistant">
            <p>⏳ Thinking...</p>
          </div>
        )}
      </div>
      {error && (
        <div style={{
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          borderRadius: '8px',
          background: '#fee2e2',
          color: '#991b1b',
          border: '1px solid #fecaca',
          fontSize: '0.875rem',
          fontWeight: '500'
        }}>
          {error}
        </div>
      )}
      <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="input"
          disabled={loading || !sessionId}
          style={{ flex: 1 }}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !input || !sessionId}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

function SummarizeInterface({ workspaceId, documents }) {
  const [selectedDocs, setSelectedDocs] = useState([])
  const [summaryType, setSummaryType] = useState('short')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (selectedDocs.length === 0 || !workspaceId) return

    setLoading(true)
    try {
      const response = await axios.post('/api/summarize/', {
        workspace_id: workspaceId,
        document_ids: selectedDocs,
        summary_type: summaryType
      })
      setResult(response.data)
    } catch (error) {
      alert('Summarization failed: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Multi-Document Summarization</h2>
      <p>Generate comprehensive summaries from multiple documents with citation provenance</p>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Select Documents</label>
          <div style={{ 
            border: '1px solid #e2e8f0', 
            borderRadius: '8px', 
            padding: '1rem',
            background: '#f8fafc',
            maxHeight: '200px',
            overflowY: 'auto'
          }}>
            {documents.filter(d => d.status === 'indexed').length === 0 ? (
              <div style={{ color: '#94a3b8', fontSize: '0.875rem', textAlign: 'center', padding: '1rem' }}>
                No indexed documents available. Upload and process documents first.
              </div>
            ) : (
              documents.filter(d => d.status === 'indexed').map(doc => (
                <label key={doc.id} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.75rem',
                  padding: '0.75rem',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  transition: 'background 0.15s',
                  marginBottom: '0.5rem'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#ffffff'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <input
                    type="checkbox"
                    checked={selectedDocs.includes(doc.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedDocs([...selectedDocs, doc.id])
                      } else {
                        setSelectedDocs(selectedDocs.filter(id => id !== doc.id))
                      }
                    }}
                    style={{ cursor: 'pointer' }}
                  />
                  <span style={{ fontSize: '0.9375rem', color: '#334155', fontWeight: '500' }}>{doc.title}</span>
                </label>
              ))
            )}
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Summary Type</label>
          <select
            value={summaryType}
            onChange={(e) => setSummaryType(e.target.value)}
            className="input"
          >
            <option value="short">Short Summary</option>
            <option value="detailed">Detailed Summary</option>
            <option value="related_work">Related Work</option>
          </select>
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading || selectedDocs.length === 0}>
          {loading ? 'Generating...' : 'Generate Summary'}
        </button>
      </form>

      {result && (
        <div className="result">
          <h3>Summary:</h3>
          <p>{result.summary}</p>
          {result.related_work && (
            <div>
              <h4>Related Work:</h4>
              <p>{result.related_work}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App

