import React, { useState, useEffect } from 'react'
import axios from 'axios'
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
      alert('Login failed: ' + (error.response?.data?.detail || error.message))
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
    return <LoginForm onLogin={handleLogin} />
  }

  return (
    <div className="container">
      <header className="header">
        <h1>PaperBot - Research Assistant</h1>
        <div>
          <span>Welcome, {user.username}</span>
          <button className="btn btn-secondary" onClick={() => {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            setUser(null)
          }}>Logout</button>
        </div>
      </header>

      <div className="workspace-selector">
        <label>Workspace: </label>
        <select
          value={selectedWorkspace?.id || ''}
          onChange={(e) => {
            const ws = workspaces.find(w => w.id === parseInt(e.target.value))
            setSelectedWorkspace(ws)
          }}
        >
          {workspaces.map(ws => (
            <option key={ws.id} value={ws.id}>{ws.name}</option>
          ))}
        </select>
      </div>

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
        <h2>Documents</h2>
        {documents.length === 0 ? (
          <p>No documents uploaded yet.</p>
        ) : (
          <ul>
            {documents.map(doc => (
              <li key={doc.id}>
                {doc.title} - {doc.status}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function LoginForm({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onLogin(username, password)
  }

  return (
    <div className="login-container">
      <div className="card">
        <h2>Login to PaperBot</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="input"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
            required
          />
          <button type="submit" className="btn btn-primary">Login</button>
        </form>
      </div>
    </div>
  )
}

function DocumentUpload({ workspaceId, onUpload }) {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [uploading, setUploading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !workspaceId) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('workspace_id', workspaceId)
    if (title) formData.append('title', title)

    try {
      await axios.post('/api/documents/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      alert('Document uploaded! Processing in background...')
      setFile(null)
      setTitle('')
      onUpload()
    } catch (error) {
      alert('Upload failed: ' + (error.response?.data?.error || error.message))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="card">
      <h2>Upload PDF Document</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files[0])}
          className="input"
          required
        />
        <input
          type="text"
          placeholder="Document title (optional)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="input"
        />
        <button type="submit" className="btn btn-primary" disabled={uploading}>
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
    </div>
  )
}

function QueryInterface({ workspaceId }) {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query || !workspaceId) return

    setLoading(true)
    try {
      const response = await axios.post('/api/query/', {
        workspace_id: workspaceId,
        query: query,
        top_k: 5
      })
      setResult(response.data)
    } catch (error) {
      alert('Query failed: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Ask a Question</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your question..."
          className="textarea"
          required
        />
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {result && (
        <div className="result">
          <h3>Answer:</h3>
          <p>{result.answer}</p>
          {result.citations && result.citations.length > 0 && (
            <div>
              <h4>Citations:</h4>
              <ul>
                {result.citations.map((cite, idx) => (
                  <li key={idx}>
                    {cite.document_title} (Page {cite.page_number || 'N/A'})
                    <br />
                    <small>{cite.snippet.substring(0, 100)}...</small>
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
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input || !sessionId) return

    const userMessage = { role: 'user', content: input }
    setMessages([...messages, userMessage])
    setInput('')
    setLoading(true)

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
      alert('Failed to send message: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Chat</h2>
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong>
            <p>{msg.content}</p>
            {msg.citations && msg.citations.length > 0 && (
              <div className="citations">
                {msg.citations.map((cite, i) => (
                  <small key={i}>{cite.document_title}</small>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={handleSend}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="input"
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" disabled={loading}>
          Send
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
      <form onSubmit={handleSubmit}>
        <div>
          <label>Select documents:</label>
          {documents.filter(d => d.status === 'indexed').map(doc => (
            <label key={doc.id}>
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
              />
              {doc.title}
            </label>
          ))}
        </div>
        <select
          value={summaryType}
          onChange={(e) => setSummaryType(e.target.value)}
          className="input"
        >
          <option value="short">Short Summary</option>
          <option value="detailed">Detailed Summary</option>
          <option value="related_work">Related Work</option>
        </select>
        <button type="submit" className="btn btn-primary" disabled={loading}>
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

