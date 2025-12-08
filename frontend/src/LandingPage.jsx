import React, { useState } from 'react'
import './LandingPage.css'

function LandingPage({ onLoginClick, onRegisterClick }) {
  const [showLogin, setShowLogin] = useState(false)
  const [showRegister, setShowRegister] = useState(false)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await onLoginClick(username, password)
      setShowLogin(false)
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    if (password !== passwordConfirm) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      await onRegisterClick(username, email, password, passwordConfirm)
      setShowRegister(false)
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="landing-nav">
        <div className="nav-container">
          <div className="logo">
            <span className="logo-icon">📚</span>
            <span className="logo-text">PaperBot</span>
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className="nav-btn-secondary" onClick={() => setShowRegister(true)}>
              Sign Up
            </button>
            <button className="nav-btn" onClick={() => setShowLogin(true)}>
              Sign In
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-container">
          <div className="hero-content">
            <h1 className="hero-title">
              Your Intelligent
              <span className="gradient-text"> Research Assistant</span>
            </h1>
            <p className="hero-subtitle">
              Transform how you interact with research papers. Upload PDFs, ask questions, 
              and get instant answers with AI-powered document understanding and citation tracking.
            </p>
            <div className="hero-buttons">
              <button className="btn-primary-large" onClick={() => setShowRegister(true)}>
                Get Started
              </button>
              <button className="btn-secondary-large" onClick={() => setShowLogin(true)}>
                Sign In
              </button>
            </div>
            <div className="hero-stats">
              <div className="stat">
                <div className="stat-number">100%</div>
                <div className="stat-label">Accurate Citations</div>
              </div>
              <div className="stat">
                <div className="stat-number">AI-Powered</div>
                <div className="stat-label">Document Analysis</div>
              </div>
              <div className="stat">
                <div className="stat-number">Instant</div>
                <div className="stat-label">Query Responses</div>
              </div>
            </div>
          </div>
          <div className="hero-visual">
            <div className="floating-card card-1">
              <div className="card-icon">📄</div>
              <div className="card-text">PDF Upload</div>
            </div>
            <div className="floating-card card-2">
              <div className="card-icon">🔍</div>
              <div className="card-text">Smart Search</div>
            </div>
            <div className="floating-card card-3">
              <div className="card-icon">💬</div>
              <div className="card-text">AI Chat</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="features-container">
          <h2 className="section-title">Powerful Features</h2>
          <p className="section-subtitle">
            Everything you need to manage and understand your research documents
          </p>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">📤</div>
              <h3 className="feature-title">Smart Upload</h3>
              <p className="feature-description">
                Upload PDF documents and let AI extract, chunk, and index content automatically
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔍</div>
              <h3 className="feature-title">RAG-Powered Q&A</h3>
              <p className="feature-description">
                Ask natural language questions and get accurate answers with source citations
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">💬</div>
              <h3 className="feature-title">Interactive Chat</h3>
              <p className="feature-description">
                Have conversations with your documents with context-aware responses
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3 className="feature-title">Multi-Doc Summaries</h3>
              <p className="feature-description">
                Generate comprehensive summaries across multiple documents with citations
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔐</div>
              <h3 className="feature-title">Secure Workspaces</h3>
              <p className="feature-description">
                Organize documents in private workspaces with enterprise-grade security
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3 className="feature-title">Lightning Fast</h3>
              <p className="feature-description">
                Powered by vector search and async processing for instant results
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-container">
          <h2 className="cta-title">Ready to Transform Your Research?</h2>
          <p className="cta-subtitle">
            Join researchers and students who are already using PaperBot to accelerate their work
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button className="btn-primary-large" onClick={() => setShowRegister(true)}>
              Start Free Trial
            </button>
            <button className="btn-secondary-large" onClick={() => setShowLogin(true)}>
              Sign In
            </button>
          </div>
        </div>
      </section>

      {/* Login Modal */}
      {showLogin && (
        <div className="modal-overlay" onClick={() => setShowLogin(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowLogin(false)}>×</button>
            <h2 className="modal-title">Welcome Back</h2>
            <p className="modal-subtitle">Sign in to your PaperBot account</p>
            <form onSubmit={handleLogin} className="login-form">
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  disabled={loading}
                />
              </div>
              {error && (
                <div className="form-error">
                  {error}
                </div>
              )}
              <button type="submit" className="btn-primary-full" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
              <p className="login-hint">
                Don't have an account?{' '}
                <button 
                  type="button" 
                  className="link-button"
                  onClick={() => {
                    setShowLogin(false)
                    setShowRegister(true)
                  }}
                >
                  Sign Up
                </button>
              </p>
              <p className="login-hint" style={{ marginTop: '0.5rem' }}>
                Demo: admin / admin123
              </p>
            </form>
          </div>
        </div>
      )}

      {/* Register Modal */}
      {showRegister && (
        <div className="modal-overlay" onClick={() => setShowRegister(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowRegister(false)}>×</button>
            <h2 className="modal-title">Create Account</h2>
            <p className="modal-subtitle">Join PaperBot and start your research journey</p>
            <form onSubmit={handleRegister} className="login-form">
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Choose a username"
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a password"
                  required
                  disabled={loading}
                  minLength={8}
                />
              </div>
              <div className="form-group">
                <label>Confirm Password</label>
                <input
                  type="password"
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  placeholder="Confirm your password"
                  required
                  disabled={loading}
                  minLength={8}
                />
              </div>
              {error && (
                <div className="form-error">
                  {error}
                </div>
              )}
              <button type="submit" className="btn-primary-full" disabled={loading}>
                {loading ? 'Creating account...' : 'Create Account'}
              </button>
              <p className="login-hint">
                Already have an account?{' '}
                <button 
                  type="button" 
                  className="link-button"
                  onClick={() => {
                    setShowRegister(false)
                    setShowLogin(true)
                  }}
                >
                  Sign In
                </button>
              </p>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default LandingPage

