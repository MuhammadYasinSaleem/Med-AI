import { useState, useEffect, useRef } from 'react'
import { Send, Loader2, X, Bot, User } from 'lucide-react'
import { conversationAPI } from '../services/api'

export default function ConversationChat({ onClose, initialMessage }) {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Initialize conversation on mount
  useEffect(() => {
    startConversation()
  }, [])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input when chat opens
  useEffect(() => {
    if (sessionId) {
      inputRef.current?.focus()
    }
  }, [sessionId])

  const startConversation = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await conversationAPI.startConversation({})
      setSessionId(response.data.session_id)
      setMessages([{
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date()
      }])
    } catch (err) {
      setError('Failed to start conversation. Please try again.')
      console.error('Start conversation error:', err)
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || !sessionId || loading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setError(null)

    // Add user message to UI immediately
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }])

    setLoading(true)

    try {
      const response = await conversationAPI.continueConversation({
        session_id: sessionId,
        message: userMessage
      })

      // Add assistant response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date(),
        stage: response.data.stage,
        symptoms: response.data.symptoms,
        suggested_workflow: response.data.suggested_workflow
      }])
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send message. Please try again.')
      console.error('Send message error:', err)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, idx) => {
        // Bold text
        line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Bullet points
        if (line.trim().startsWith('•')) {
          return `<div class="flex items-start gap-2"><span class="text-[#4285f4] mt-1">•</span><span>${line.substring(1).trim()}</span></div>`
        }
        return line ? `<div>${line}</div>` : '<br/>'
      })
      .join('')
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#e8eaed]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#e8f0fe] flex items-center justify-center">
              <Bot className="w-5 h-5 text-[#4285f4]" />
            </div>
            <div>
              <h2 className="font-semibold text-[#202124]">MedAI Assistant</h2>
              <p className="text-xs text-[#5f6368]">
                {sessionId ? 'Conversation active' : 'Starting conversation...'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-[#f1f3f4] transition-colors"
          >
            <X className="w-5 h-5 text-[#5f6368]" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-[#e8f0fe] flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-[#4285f4]" />
                </div>
              )}
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-[#4285f4] text-white'
                    : 'bg-[#f8f9fa] text-[#202124]'
                }`}
              >
                <div
                  className="text-sm leading-relaxed whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
                />
                {msg.symptoms && msg.symptoms.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-[#e8eaed]">
                    <p className="text-xs text-[#5f6368]">
                      Detected symptoms: {msg.symptoms.join(', ')}
                    </p>
                  </div>
                )}
                {msg.suggested_workflow && (
                  <div className="mt-2 pt-2 border-t border-[#e8eaed]">
                    <p className="text-xs text-[#5f6368]">
                      Suggested workflow: <span className="font-medium">{msg.suggested_workflow}</span>
                    </p>
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-[#4285f4] flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-[#e8f0fe] flex items-center justify-center">
                <Bot className="w-4 h-4 text-[#4285f4]" />
              </div>
              <div className="bg-[#f8f9fa] rounded-2xl px-4 py-3">
                <Loader2 className="w-5 h-5 text-[#4285f4] animate-spin" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="px-4 pb-2">
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-[#e8eaed]">
          <form onSubmit={sendMessage} className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2 border border-[#dfe1e5] rounded-full focus:outline-none focus:ring-2 focus:ring-[#4285f4] focus:border-transparent"
              disabled={loading || !sessionId}
            />
            <button
              type="submit"
              disabled={loading || !sessionId || !inputMessage.trim()}
              className="px-6 py-2 bg-[#4285f4] text-white rounded-full hover:bg-[#1967d2] disabled:bg-[#9aa0a6] disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span className="hidden sm:inline">Send</span>
                </>
              )}
            </button>
          </form>
          <p className="text-xs text-[#9aa0a6] mt-2 text-center">
            Powered by MedAI Orchestrator • Ask about symptoms, lab reports, or medications
          </p>
        </div>
      </div>
    </div>
  )
}
