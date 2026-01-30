import { useState, useRef, useEffect } from 'react'
import { MessageSquare, Send, Loader2, CheckCircle, Download, Activity, Search, User } from 'lucide-react'
import { interviewAPI } from '../services/api'

const API_BASE_URL = 'http://localhost:8000'

export default function Interview() {
  const [activeTab, setActiveTab] = useState('interview') // 'interview' or 'triage'
  
  // Interview state
  const [sessionId, setSessionId] = useState(null)
  const [language, setLanguage] = useState('English')
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [conversation, setConversation] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  
  // Triage state
  const [triageSymptoms, setTriageSymptoms] = useState('')
  const [triageLoading, setTriageLoading] = useState(false)
  const [triageError, setTriageError] = useState(null)
  const [triageResult, setTriageResult] = useState(null)
  
  // Refs for auto-scroll
  const messagesEndRef = useRef(null)
  const answerInputRef = useRef(null)
  
  // Auto-scroll to bottom when conversation updates
  useEffect(() => {
    if (sessionId) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [conversation, sessionId])

  const startInterview = async () => {
    setLoading(true)
    setError(null)
    setConversation([])
    setSummary(null)

    try {
      // Map language display name to backend format
      const languageMap = {
        'English': 'English',
        'Urdu': 'Urdu',
        //'Spanish': 'Spanish',
        'Roman Urdu': 'Roman Urdu',
      }
      const backendLanguage = languageMap[language] || 'English'
      
      const response = await interviewAPI.startInterview({ language: backendLanguage })
      setSessionId(response.data.session_id)
      
      if (response.data.agent_message) {
        setCurrentQuestion(response.data.agent_message)
        setConversation([{ type: 'agent', message: response.data.agent_message }])
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start interview')
    } finally {
      setLoading(false)
    }
  }

  const submitAnswer = async () => {
    if (!answer.trim() || !sessionId) return

    setLoading(true)
    setError(null)

    const userMessage = answer
    setConversation(prev => [...prev, { type: 'user', message: userMessage }])
    setAnswer('')

    try {
      const response = await interviewAPI.submitAnswer({
        session_id: sessionId,
        answer: userMessage,
      })

      if (response.data.next_step === 'generate_summary') {
        await generateSummary()
      } else if (response.data.next_question) {
        setCurrentQuestion(response.data.next_question)
        setConversation(prev => [...prev, { type: 'agent', message: response.data.next_question }])
      } else if (response.data.message) {
        setConversation(prev => [...prev, { type: 'system', message: response.data.message }])
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit answer')
    } finally {
      setLoading(false)
    }
  }

  const generateSummary = async () => {
    if (!sessionId) return

    setLoading(true)
    setError(null)

    try {
      const response = await interviewAPI.generateSummary({ session_id: sessionId })
      setSummary(response.data)
      setConversation(prev => [...prev, { 
        type: 'system', 
        message: 'Interview completed. Summary generated.' 
      }])
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate summary')
    } finally {
      setLoading(false)
    }
  }

  // Helper function to normalize PDF URL (handle both old media URLs and new API endpoints)
  const getPdfUrl = (pdfUrl) => {
    if (!pdfUrl) return null
    
    // If it's already a full URL, return as is
    if (pdfUrl.startsWith('http://') || pdfUrl.startsWith('https://')) {
      return pdfUrl
    }
    
    // If it's the old media URL format (/media/reports/...), convert to API endpoint
    if (pdfUrl.startsWith('/media/reports/session_')) {
      const match = pdfUrl.match(/session_(\d+)_soap\.pdf/)
      if (match) {
        const sessionId = match[1]
        return `${API_BASE_URL}/medai/interview/pdf/${sessionId}/`
      }
    }
    
    // If it's already the new API endpoint format, just prepend base URL
    if (pdfUrl.startsWith('/medai/interview/pdf/')) {
      return `${API_BASE_URL}${pdfUrl}`
    }
    
    // Default: prepend base URL
    return `${API_BASE_URL}${pdfUrl}`
  }

  const performTriage = async () => {
    if (!triageSymptoms.trim()) {
      setTriageError('Please enter symptoms for triage assessment')
      return
    }

    setTriageLoading(true)
    setTriageError(null)
    setTriageResult(null)

    try {
      const response = await interviewAPI.triage({ text: triageSymptoms })
      setTriageResult(response.data)
    } catch (err) {
      setTriageError(err.response?.data?.error || 'Failed to perform triage')
    } finally {
      setTriageLoading(false)
    }
  }

  // If interview is active, show Gemini-style chat interface
  if (activeTab === 'interview' && sessionId) {
    return (
      <div className="h-screen bg-white dark:bg-[#1a1a1a] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#e2e8f0] dark:border-[#5f6368] flex-shrink-0">
          <div className="flex items-center gap-3">
            <div>
              <h2 className="font-semibold text-[#1a1a1a] dark:text-[#e8eaed]">Patient Interview</h2>
              <p className="text-xs text-[#4a5568] dark:text-[#9aa0a6]">
                {loading ? 'Processing...' : 'Interview in progress'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setActiveTab('triage')
                setSessionId(null)
                setSummary(null)
                setError(null)
                setConversation([])
                setCurrentQuestion('')
                setAnswer('')
              }}
              className="px-4 py-2 text-sm text-[#4a5568] dark:text-[#9aa0a6] hover:text-[#1a1a1a] dark:hover:text-[#e8eaed] transition-colors"
            >
              Switch to Triage
            </button>
          </div>
        </div>

        {/* Messages - Gemini Style */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-white dark:bg-[#1a1a1a]">
          {conversation.map((item, idx) => (
            <div
              key={idx}
              className={`flex gap-4 max-w-3xl mx-auto ${
                item.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                  item.type === 'user'
                    ? 'bg-[#4285f4] dark:bg-[#1a73e8] text-white'
                    : item.type === 'system'
                    ? 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300 border border-yellow-200 dark:border-yellow-800'
                    : 'bg-[#f7fafc] dark:bg-[#303134] text-[#1a1a1a] dark:text-[#e8eaed] border border-[#e2e8f0] dark:border-[#5f6368]'
                }`}
              >
                <p className={`text-sm leading-relaxed whitespace-pre-wrap ${
                  item.type === 'user' ? 'text-white' : ''
                }`}>{item.message}</p>
              </div>
              {item.type === 'user' && (
                <div className="w-8 h-8 rounded-full bg-[#4285f4] dark:bg-[#1a73e8] flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex gap-4 justify-start max-w-3xl mx-auto">
              <div className="bg-[#f7fafc] dark:bg-[#303134] rounded-2xl px-4 py-3 border border-[#e2e8f0] dark:border-[#5f6368]">
                <Loader2 className="w-5 h-5 text-[#4285f4] dark:text-[#8ab4f8] animate-spin" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="px-4 pb-2 flex-shrink-0">
            <div className="max-w-3xl mx-auto bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          </div>
        )}

        {/* Input Area - Gemini Style */}
        <div className="p-4 border-t border-[#e2e8f0] dark:border-[#5f6368] bg-white dark:bg-[#1a1a1a] flex-shrink-0">
          <div className="max-w-3xl mx-auto">
            {currentQuestion && (
              <div className="mb-3">
                <textarea
                  ref={answerInputRef}
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Type your answer..."
                  className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-colors placeholder-[#9aa0a6] dark:placeholder-[#5f6368] resize-none"
                  rows="3"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      if (!loading && answer.trim()) {
                        submitAnswer()
                      }
                    }
                  }}
                />
              </div>
            )}
            <div className="flex items-center gap-2">
              <div className="relative flex items-center flex-1 h-14 px-5 rounded-full border border-[#e2e8f0] dark:border-[#5f6368] bg-white dark:bg-[#202124] shadow-sm hover:shadow-md transition-all">
                <Search className="w-5 h-5 text-[#718096] dark:text-[#9aa0a6] mr-3 flex-shrink-0" />
                {currentQuestion ? (
                  <input
                    type="text"
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Type your answer..."
                    className="flex-1 outline-none text-[#1a1a1a] dark:text-[#e8eaed] text-base bg-transparent placeholder-[#718096] dark:placeholder-[#9aa0a6]"
                    disabled={loading}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        if (!loading && answer.trim()) {
                          submitAnswer()
                        }
                      }
                    }}
                  />
                ) : (
                  <input
                    type="text"
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Waiting for question..."
                    className="flex-1 outline-none text-[#1a1a1a] dark:text-[#e8eaed] text-base bg-transparent placeholder-[#718096] dark:placeholder-[#9aa0a6]"
                    disabled={true}
                  />
                )}
                <button
                  onClick={submitAnswer}
                  disabled={loading || !answer.trim() || !currentQuestion}
                  className="ml-3 px-4 py-2 bg-[#4285f4] dark:bg-[#1a73e8] text-white rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] disabled:bg-[#a0aec0] disabled:cursor-not-allowed flex items-center gap-2 transition-colors font-medium"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
              {conversation.length > 0 && (
                <button
                  onClick={generateSummary}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-full hover:bg-green-700 dark:hover:bg-green-800 disabled:bg-[#9aa0a6] disabled:cursor-not-allowed flex items-center gap-2 transition-colors font-medium shadow-md hover:shadow-lg"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span className="hidden sm:inline">Summary</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Summary Display - Overlay Style */}
        {summary && (
          <div className="absolute inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-[#303134] rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                  <h2 className="text-2xl font-semibold text-[#202124] dark:text-[#e8eaed]">Clinical Summary</h2>
                </div>
                <button
                  onClick={() => setSummary(null)}
                  className="text-[#5f6368] dark:text-[#9aa0a6] hover:text-[#202124] dark:hover:text-[#e8eaed]"
                >
                  ×
                </button>
              </div>
              {summary.soap_note && (
                <div className="mb-4">
                  <h3 className="font-semibold text-[#202124] dark:text-[#e8eaed] mb-2">SOAP Note</h3>
                  <p className="text-[#5f6368] dark:text-[#9aa0a6] whitespace-pre-wrap leading-relaxed">{summary.soap_note}</p>
                </div>
              )}
              {summary.pdf_url && (
                <a
                  href={getPdfUrl(summary.pdf_url)}
                  target="_blank"
                  rel="noopener noreferrer"
                  download
                  className="inline-flex items-center gap-2 px-4 py-2 bg-[#4285f4] dark:bg-[#1a73e8] text-white rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] transition-colors font-medium shadow-md hover:shadow-lg"
                >
                  <Download className="w-4 h-4" />
                  Download PDF Report
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="px-4 py-8 min-h-screen bg-white dark:bg-[#1a1a1a]">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-[#202124] dark:text-[#e8eaed] mb-6">Patient Interview & Triage</h1>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 border-b border-[#e2e8f0] dark:border-[#5f6368]">
          <button
            onClick={() => {
              setActiveTab('interview')
              setTriageResult(null)
              setTriageError(null)
            }}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'interview'
                ? 'border-[#4285f4] dark:border-[#8ab4f8] text-[#4285f4] dark:text-[#8ab4f8]'
                : 'border-transparent text-[#5f6368] dark:text-[#9aa0a6] hover:text-[#202124] dark:hover:text-[#e8eaed]'
            }`}
          >
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              <span>Patient Interview</span>
            </div>
          </button>
          <button
            onClick={() => {
              setActiveTab('triage')
              setSessionId(null)
              setSummary(null)
              setError(null)
            }}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'triage'
                ? 'border-[#4285f4] dark:border-[#8ab4f8] text-[#4285f4] dark:text-[#8ab4f8]'
                : 'border-transparent text-[#5f6368] dark:text-[#9aa0a6] hover:text-[#202124] dark:hover:text-[#e8eaed]'
            }`}
          >
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              <span>Triage Assessment</span>
            </div>
          </button>
        </div>

        {/* Interview Tab Content - Start Screen */}
        {activeTab === 'interview' && !sessionId && (
          <>
            {/* Start Interview Section - Gemini Style */}
            <div className="flex flex-col items-center justify-center min-h-[60vh]">
              <div className="text-center mb-8">
                <h2 className="text-4xl font-semibold text-[#202124] dark:text-[#e8eaed] mb-2">Patient Interview</h2>
                <p className="text-[#5f6368] dark:text-[#9aa0a6]">
                  Conduct a structured interview to gather comprehensive patient information
                </p>
              </div>
              
              <div className="w-full max-w-md space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-2">
                    Select Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-full focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-colors shadow-sm hover:shadow-md"
                  >
                    <option value="English">English</option>
                    <option value="Urdu">Urdu</option>
                    <option value="Roman Urdu">Roman Urdu</option>
                  </select>
                </div>
                <button
                  onClick={startInterview}
                  disabled={loading}
                  className="w-full bg-[#4285f4] dark:bg-[#1a73e8] text-white py-3 px-6 rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] disabled:bg-[#9aa0a6] disabled:cursor-not-allowed flex items-center justify-center transition-colors font-medium shadow-md hover:shadow-lg"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <MessageSquare className="w-5 h-5 mr-2" />
                      Start Interview
                    </>
                  )}
                </button>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mt-6 max-w-md w-full bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                </div>
              )}
            </div>
          </>
        )}

        {/* Triage Tab Content - Gemini Style */}
        {activeTab === 'triage' && (
          <>
            {/* Main Triage Input Section */}
            {!triageResult && (
              <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <div className="text-center mb-8">
                  <h2 className="text-4xl font-semibold text-[#202124] dark:text-[#e8eaed] mb-2">Triage Assessment</h2>
                  <p className="text-[#5f6368] dark:text-[#9aa0a6]">
                    Quickly assess patient urgency and priority level based on reported symptoms
                  </p>
                </div>
                
                <div className="w-full max-w-2xl space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-3">
                      Enter Patient Symptoms
                    </label>
                    <div className="relative">
                      <textarea
                        value={triageSymptoms}
                        onChange={(e) => setTriageSymptoms(e.target.value)}
                        placeholder="Describe the patient's symptoms (e.g., chest pain, difficulty breathing, high fever)..."
                        className="w-full px-6 py-4 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md placeholder-[#9aa0a6] dark:placeholder-[#5f6368] resize-none"
                        rows="6"
                      />
                    </div>
                  </div>
                  
                  <button
                    onClick={performTriage}
                    disabled={triageLoading || !triageSymptoms.trim()}
                    className="w-full bg-[#4285f4] dark:bg-[#1a73e8] text-white py-4 px-6 rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] disabled:bg-[#9aa0a6] disabled:cursor-not-allowed flex items-center justify-center transition-colors font-medium shadow-md hover:shadow-lg text-base"
                  >
                    {triageLoading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Analyzing Symptoms...
                      </>
                    ) : (
                      <>
                        <Activity className="w-5 h-5 mr-2" />
                        Perform Triage Assessment
                      </>
                    )}
                  </button>
                </div>

                {/* Triage Error Display */}
                {triageError && (
                  <div className="mt-6 max-w-2xl w-full bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-4">
                    <p className="text-sm text-red-700 dark:text-red-300 text-center">{triageError}</p>
                  </div>
                )}
              </div>
            )}

            {/* Triage Result Display - Gemini Style */}
            {triageResult && (
              <div className="flex flex-col items-center justify-center min-h-[60vh] py-8">
                <div className="w-full max-w-2xl space-y-6">
                  {/* Result Header */}
                  <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#e8f0fe] dark:bg-[#303134] mb-4">
                      <Activity className="w-8 h-8 text-[#4285f4] dark:text-[#8ab4f8]" />
                    </div>
                    <h2 className="text-3xl font-semibold text-[#202124] dark:text-[#e8eaed] mb-2">Assessment Complete</h2>
                    <p className="text-[#5f6368] dark:text-[#9aa0a6]">Triage assessment results</p>
                  </div>

                  {/* Result Card */}
                  <div className="bg-white dark:bg-[#303134] rounded-2xl shadow-lg p-8 border border-[#e2e8f0] dark:border-[#5f6368]">
                    <div className="space-y-6">
                      {/* Priority Level */}
                      <div className="flex items-center justify-between p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                        <div>
                          <span className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-1">
                            Priority Level
                          </span>
                          <span className={`inline-block font-bold text-2xl px-5 py-2 rounded-full mt-2 ${
                            triageResult.triage === 'IMMEDIATE' || triageResult.triage === 'VERY_URGENT' 
                              ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' 
                              : triageResult.triage === 'URGENT' 
                              ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                              : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          }`}>
                            {triageResult.triage}
                          </span>
                        </div>
                        <div className={`w-4 h-4 rounded-full ${
                          triageResult.triage === 'IMMEDIATE' || triageResult.triage === 'VERY_URGENT' 
                            ? 'bg-red-500' 
                            : triageResult.triage === 'URGENT' 
                            ? 'bg-orange-500'
                            : 'bg-green-500'
                        }`} />
                      </div>
                      
                      {/* Message */}
                      {triageResult.message && (
                        <div className="p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                          <p className="text-[#202124] dark:text-[#e8eaed] leading-relaxed whitespace-pre-wrap">
                            {triageResult.message}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-4">
                    <button
                      onClick={() => {
                        setTriageResult(null)
                        setTriageSymptoms('')
                        setTriageError(null)
                      }}
                      className="flex-1 bg-white dark:bg-[#303134] text-[#4285f4] dark:text-[#8ab4f8] border border-[#4285f4] dark:border-[#8ab4f8] py-3 px-6 rounded-full hover:bg-[#f8f9fa] dark:hover:bg-[#202124] transition-colors font-medium shadow-sm hover:shadow-md"
                    >
                      New Assessment
                    </button>
                    <button
                      onClick={() => {
                        setActiveTab('interview')
                        setTriageResult(null)
                        setTriageSymptoms('')
                        setTriageError(null)
                      }}
                      className="flex-1 bg-[#4285f4] dark:bg-[#1a73e8] text-white py-3 px-6 rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] transition-colors font-medium shadow-md hover:shadow-lg"
                    >
                      Start Interview
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
