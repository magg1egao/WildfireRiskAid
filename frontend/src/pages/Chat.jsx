import { useState, useRef, useEffect } from 'react'

const SUGGESTION_GROUPS = [
  {
    label: 'Risk Assessment',
    icon: 'fas fa-fire',
    items: ['Summarize current risks', 'Show critical zones', 'Risk trend analysis'],
  },
  {
    label: 'Vegetation',
    icon: 'fas fa-leaf',
    items: ['Analyze vegetation health', 'NDVI decline explanation', 'Burn ratio status'],
  },
  {
    label: 'Weather Impact',
    icon: 'fas fa-wind',
    items: ['Weather forecast impact', 'Wind conditions effect', 'Humidity analysis'],
  },
]

const INITIAL_MSG = {
  role: 'ai',
  text: 'Welcome to FireSight AI Assistant. I can help you analyze wildfire risks, interpret vegetation indices, understand weather impacts, and more. What would you like to know?',
}

function formatText(text) {
  const paragraphs = text.split('\n\n').filter((p) => p.trim())
  return paragraphs.map((p, i) => {
    if (p.includes('- ')) {
      const lines = p.split('\n')
      return (
        <ul key={i}>
          {lines.map((line, j) =>
            line.startsWith('- ') ? (
              <li key={j}>{line.substring(2)}</li>
            ) : line.trim() ? (
              <p key={j}>{line}</p>
            ) : null
          )}
        </ul>
      )
    }
    return <p key={i}>{p.replace(/\n/g, ' ')}</p>
  })
}

export default function Chat() {
  const [messages, setMessages] = useState([INITIAL_MSG])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    const analysis = localStorage.getItem('firesight_gpt_analysis')
    if (analysis) {
      setMessages((prev) => [
        ...prev,
        { role: 'ai', text: '📊 Analysis of Uploaded Data:\n\n' + analysis },
      ])
      localStorage.removeItem('firesight_gpt_analysis')
    }
  }, [])

  async function sendMessage(text) {
    const query = (text !== undefined ? text : input).trim()
    if (!query || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: query }])
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'ai', text: data.answer }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'ai', text: 'Sorry, I encountered an error. Please try again.' },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="chat-page">
      {/* Sidebar */}
      <aside className="chat-sidebar">
        <div className="chat-sidebar-header">
          <div className="chat-ai-identity">
            <div className="chat-ai-avatar">
              <i className="fas fa-robot"></i>
            </div>
            <div>
              <div className="chat-ai-name">FireSight AI</div>
              <div className="chat-ai-tagline">Wildfire risk assistant</div>
            </div>
          </div>
        </div>

        <div className="chat-context">
          <div className="chat-context-label">Current Conditions</div>
          <div className="chat-context-card">
            <span className="chat-context-card-label">Risk Level</span>
            <span className="chat-context-card-value" style={{ color: 'var(--risk-high)' }}>HIGH</span>
          </div>
          <div className="chat-context-card">
            <span className="chat-context-card-label">Active Alerts</span>
            <span className="chat-context-card-value" style={{ color: 'var(--danger)' }}>3</span>
          </div>
          <div className="chat-context-card">
            <span className="chat-context-card-label">Avg NDVI</span>
            <span className="chat-context-card-value" style={{ color: 'var(--warning)' }}>0.52</span>
          </div>
        </div>

        <div className="chat-suggestions">
          {SUGGESTION_GROUPS.map((group) => (
            <div key={group.label} className="chat-suggestion-group">
              <div className="chat-suggestion-group-label">
                <i className={group.icon}></i>
                {group.label}
              </div>
              {group.items.map((item) => (
                <button
                  key={item}
                  className="chat-suggestion-btn"
                  onClick={() => sendMessage(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          ))}
        </div>

        <div className="chat-sidebar-footer">
          <button className="chat-clear-btn" onClick={() => setMessages([INITIAL_MSG])}>
            <i className="fas fa-trash-alt"></i>
            Clear conversation
          </button>
        </div>
      </aside>

      {/* Main chat area */}
      <div className="chat-main">
        <div className="chat-messages-area">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div className="chat-msg-avatar">
                <i className={msg.role === 'ai' ? 'fas fa-robot' : 'fas fa-user'}></i>
              </div>
              <div className="chat-bubble">
                {msg.role === 'ai' ? formatText(msg.text) : <p>{msg.text}</p>}
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-msg ai">
              <div className="chat-msg-avatar">
                <i className="fas fa-robot"></i>
              </div>
              <div className="chat-bubble">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-composer">
          <div className="chat-composer-inner">
            <textarea
              ref={inputRef}
              className="chat-composer-input"
              placeholder="Ask about wildfire risks, terrain analysis, or request summaries..."
              value={input}
              rows={1}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              className="chat-send-btn"
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
            >
              <i className="fas fa-paper-plane"></i>
            </button>
          </div>
          <div className="chat-composer-hint">Enter to send · Shift+Enter for new line</div>
        </div>
      </div>
    </div>
  )
}
