import { useState, useRef, useEffect } from 'react'

const SUGGESTIONS = [
  'Summarize current risks',
  'Analyze vegetation health',
  'Weather forecast impact',
  'Show critical zones',
]

function formatResponse(text) {
  const paragraphs = text.split('\n\n').filter((p) => p.trim() !== '')
  return paragraphs.map((p, i) => {
    if (p.includes('- ')) {
      const lines = p.split('\n')
      return (
        <ul key={i}>
          {lines.map((line, j) =>
            line.startsWith('- ') ? (
              <li key={j}>{line.substring(2)}</li>
            ) : (
              <p key={j}>{line}</p>
            )
          )}
        </ul>
      )
    }
    return <p key={i}>{p.replace(/\n/g, ' ')}</p>
  })
}

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    { role: 'system', text: 'Welcome to FireSight AI Assistant. How can I help with your wildfire assessment today?' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Show GPT analysis from localStorage on mount
  useEffect(() => {
    const analysis = localStorage.getItem('firesight_gpt_analysis')
    if (analysis) {
      setMessages((prev) => [
        ...prev,
        { role: 'system', text: '📊 Analysis of Uploaded Data:\n\n' + analysis },
      ])
      localStorage.removeItem('firesight_gpt_analysis')
    }
  }, [])

  async function sendMessage(text) {
    const query = text || input.trim()
    if (!query) return

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
      setMessages((prev) => [...prev, { role: 'system', text: data.answer }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'system', text: 'Sorry, I encountered an error. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyPress(e) {
    if (e.key === 'Enter') sendMessage()
  }

  return (
    <div className="panel panel-dark" style={{ marginTop: 20 }}>
      <div className="panel-header">
        <div className="panel-title">
          <i className="fas fa-robot"></i>
          FireSight AI Assistant
        </div>
        <div className="panel-actions">
          <button className="btn btn-sm btn-outline-light">
            <i className="fas fa-history"></i>
            <span className="hide-mobile"> History</span>
          </button>
        </div>
      </div>
      <div className="panel-body" style={{ padding: 0 }}>
        <div className="chatbot-container">
          <div className="chatbot-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chatbot-message ${msg.role}`}>
                <div className="chatbot-message-content">
                  {msg.role === 'system' ? formatResponse(msg.text) : <p>{msg.text}</p>}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chatbot-message system">
                <div className="chatbot-message-content">
                  <p>FireSight AI is thinking...</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chatbot-suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="suggestion-chip" onClick={() => sendMessage(s)}>
                {s}
              </button>
            ))}
          </div>

          <div className="chatbot-footer">
            <input
              type="text"
              className="chatbot-input"
              placeholder="Ask about wildfire risks, terrain analysis, or request summaries..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button className="chatbot-button" onClick={() => sendMessage()}>
              <i className="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
