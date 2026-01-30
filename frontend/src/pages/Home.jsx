import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Send, Loader2, User, X, FileText, MessageSquare, Pill, Volume2, VolumeX, Activity, Square, Mic } from 'lucide-react'
import { interviewAPI, medicationAPI } from '../services/api'

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const [conversationMode, setConversationMode] = useState(false)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const speechSynthesisRef = useRef(null)
  const speechRecognitionRef = useRef(null)
  const navigate = useNavigate()
  
  // Speech-to-text state
  const [isListening, setIsListening] = useState(false)
  
  // Flow state management
  const [triageDone, setTriageDone] = useState(false)
  const [triageLevel, setTriageLevel] = useState(null)
  const [triageMessage, setTriageMessage] = useState(null)
  const [interviewSessionId, setInterviewSessionId] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [interviewInProgress, setInterviewInProgress] = useState(false)
  const [soapNote, setSoapNote] = useState(null)
  const [soapPdfUrl, setSoapPdfUrl] = useState(null)

  const quickActions = [
    {
      title: 'Analyze Lab Report',
      icon: FileText,
      path: '/lab-analyzer',
      description: 'Upload and analyze lab reports',
    },
    {
      title: 'Start Interview',
      icon: MessageSquare,
      path: '/interview',
      description: 'Patient interview & triage',
    },
    {
      title: 'Triage Assessment',
      icon: Activity,
      path: '/triage',
      description: 'Assess symptom urgency',
    },
    {
      title: 'Check Medications',
      icon: Pill,
      path: '/medication-interaction',
      description: 'Drug interaction checker',
    },
  ]

  // Initialize conversation when entering conversation mode
  useEffect(() => {
    if (conversationMode && !triageDone) {
      // Show initial greeting
      setMessages([{
        role: 'assistant',
        content: "Hello! I'm here to help assess your medical situation. Please describe your symptoms or concerns, and I'll perform a triage assessment to determine the appropriate care pathway.",
        timestamp: new Date()
      }])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationMode])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (conversationMode) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, conversationMode])

  // Focus input when conversation mode starts
  useEffect(() => {
    if (conversationMode && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [conversationMode])

  // Text-to-speech function
  const speakText = (text) => {
    if (!voiceEnabled || !('speechSynthesis' in window)) return

    // Stop any ongoing speech
    if (speechSynthesisRef.current) {
      window.speechSynthesis.cancel()
    }

    // Clean text - remove markdown and HTML tags
    const cleanText = text
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
      .replace(/•/g, '') // Remove bullet points
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/\n/g, ' ') // Replace newlines with spaces
      .trim()

    if (!cleanText) return

    const utterance = new SpeechSynthesisUtterance(cleanText)
    
    // Configure voice settings
    utterance.rate = 1.0 // Normal speed
    utterance.pitch = 1.0 // Normal pitch
    utterance.volume = 1.0 // Full volume

    // Try to use a natural-sounding voice
    const voices = window.speechSynthesis.getVoices()
    const preferredVoices = voices.filter(voice => 
      voice.lang.startsWith('en') && 
      (voice.name.includes('Natural') || voice.name.includes('Premium') || voice.name.includes('Enhanced'))
    )
    
    if (preferredVoices.length > 0) {
      utterance.voice = preferredVoices[0]
    } else if (voices.length > 0) {
      // Fallback to first English voice
      const englishVoices = voices.filter(voice => voice.lang.startsWith('en'))
      if (englishVoices.length > 0) {
        utterance.voice = englishVoices[0]
      }
    }

    utterance.onstart = () => {
      setIsSpeaking(true)
      speechSynthesisRef.current = utterance
    }

    utterance.onend = () => {
      setIsSpeaking(false)
      speechSynthesisRef.current = null
    }

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event)
      setIsSpeaking(false)
      speechSynthesisRef.current = null
    }

    window.speechSynthesis.speak(utterance)
  }

  // Stop speaking
  const stopSpeaking = () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      speechSynthesisRef.current = null
    }
  }

  // Toggle voice on/off
  const toggleVoice = () => {
    if (voiceEnabled && isSpeaking) {
      stopSpeaking()
    }
    setVoiceEnabled(!voiceEnabled)
  }

  // Load voices when component mounts
  useEffect(() => {
    if ('speechSynthesis' in window) {
      // Some browsers need voices to be loaded
      const loadVoices = () => {
        window.speechSynthesis.getVoices()
      }
      loadVoices()
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices
      }
    }
  }, [])

  // Speak assistant messages when they arrive
  useEffect(() => {
    if (conversationMode && messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.role === 'assistant' && voiceEnabled) {
        // Small delay to ensure message is rendered
        setTimeout(() => {
          speakText(lastMessage.content)
        }, 300)
      }
    }
  }, [messages, conversationMode, voiceEnabled])

  // Speech recognition functions
  const stopListening = () => {
    if (speechRecognitionRef.current && isListening) {
      speechRecognitionRef.current.stop()
      setIsListening(false)
    }
  }

  const startListening = () => {
    if (!speechRecognitionRef.current) {
      setError('Speech recognition is not supported in this browser.')
      return
    }

    try {
      speechRecognitionRef.current.start()
    } catch (err) {
      console.error('Error starting speech recognition:', err)
      setError('Failed to start speech recognition. Please try again.')
    }
  }

  const toggleListening = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // @ts-ignore - SpeechRecognition API types
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        recognition.continuous = false
        recognition.interimResults = false
        recognition.lang = 'en-US' // English only

        recognition.onstart = () => {
          setIsListening(true)
        }

        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript
          setSearchQuery(prev => prev ? `${prev} ${transcript}` : transcript)
          setIsListening(false)
        }

        recognition.onerror = (event) => {
          console.error('Speech recognition error:', event.error)
          setIsListening(false)
          if (event.error === 'no-speech') {
            setError('No speech detected. Please try again.')
          } else if (event.error === 'not-allowed') {
            setError('Microphone permission denied. Please enable microphone access.')
          }
        }

        recognition.onend = () => {
          setIsListening(false)
        }

        speechRecognitionRef.current = recognition
      }
    }
  }, [])

  // Cleanup speech on unmount or exit conversation
  useEffect(() => {
    return () => {
      stopSpeaking()
      stopListening()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])


  // Detect medication/prescription-related queries
  const isMedicationQuery = (message) => {
    const lowerMessage = message.toLowerCase()
    const medicationKeywords = [
      'can i get', 'get medicine', 'get medication', 'prescribe', 'prescription', 
      'what medicine', 'which medicine', 'what medication', 'which medication',
      'give me medicine', 'give me medication', 'need medicine', 'need medication',
      'recommend medicine', 'recommend medication', 'suggest medicine', 'suggest medication',
      'should i take', 'should i use', 'can i take', 'can i use', 'interaction', 'interact'
    ]
    return medicationKeywords.some(keyword => lowerMessage.includes(keyword))
  }

  // Analyze medication query type
  const analyzeMedicationQuery = (message) => {
    const lowerMessage = message.toLowerCase()
    
    // Check if asking for prescription/new medication
    const prescriptionKeywords = ['can i get', 'get medicine', 'get medication', 'prescribe', 'prescription', 
      'give me', 'need medicine', 'need medication', 'recommend', 'suggest']
    const isPrescriptionRequest = prescriptionKeywords.some(keyword => lowerMessage.includes(keyword))
    
    // Check if asking about interactions
    const interactionKeywords = ['interaction', 'interact', 'check', 'taking', 'with']
    const isInteractionRequest = interactionKeywords.some(keyword => lowerMessage.includes(keyword))
    
    // Check if mentions existing medications
    const hasExistingMeds = /\b(taking|take|on|using|use)\b.*\b(medication|medicine|pill|drug|tablet|capsule)\b/i.test(message)
    
    return {
      isPrescriptionRequest,
      isInteractionRequest,
      hasExistingMeds,
      message
    }
  }

  // Handle medication queries appropriately with contextual responses
  const handleMedicationQuery = async (userMessage) => {
    const analysis = analyzeMedicationQuery(userMessage)
    let response = ''
    
    if (analysis.isPrescriptionRequest) {
      // User is asking for a prescription/new medication
      response = `I understand you're asking about medications for your condition. I need to clarify my role:\n\n**Important:** I am a clinical decision-support tool and medical intake assistant - I **cannot prescribe, recommend, or suggest specific medications**. Only licensed healthcare professionals can determine appropriate treatment.\n\n**However, I can help you in these ways:**\n\n• **Assess your symptoms** - I can perform a triage assessment to determine the urgency of your situation and help guide you to the appropriate care pathway\n• **Gather information** - I can conduct an interview to collect your medical information and prepare a clinical summary for your doctor's visit\n• **Support decision-making** - I can help you understand when you should seek immediate medical care vs. when it's appropriate to schedule a regular appointment\n\n**What I recommend:**\nLet me help assess your symptoms first. Describe what you're experiencing, and I'll:\n1. Perform a triage assessment\n2. Conduct a medical interview to gather relevant information\n3. Generate a clinical summary that you can take to your healthcare provider\n\nThis will help your doctor make an informed decision about the best treatment, including medications if needed.\n\nPlease describe your symptoms or concerns.`
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response,
        timestamp: new Date()
      }])
      
      // After explaining, the user can describe symptoms and we'll proceed with triage
      // The conversation flow will continue naturally
      
    } else if (analysis.isInteractionRequest || analysis.hasExistingMeds) {
      // User wants to check medication interactions
      response = `I can help you check for medication interactions! However, for a complete interaction analysis, I'll need some additional information:\n\n**To check interactions, please provide:**\n• **Your current medications** (names of all medications you're taking)\n• **Your age**\n• **Any medical conditions** you have (e.g., diabetes, high blood pressure, kidney disease)\n• **If any medications are new** (recently prescribed or considering)\n\n**You have two options:**\n\n1. **Use the Medication Interaction Checker** (recommended for detailed analysis):\n   - Go to the "Check Medications" option in the menu above\n   - Fill out the form with your medications and medical information\n   - Get a comprehensive interaction analysis with visual graphs\n\n2. **Continue here**: If you'd like, you can tell me about your medications and I can help guide you, but for a full analysis with interaction graphs, the dedicated tool is better.\n\nWould you like me to help assess your symptoms instead, or would you prefer to use the Medication Interaction Checker tool?`
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response,
        timestamp: new Date()
      }])
    } else {
      // General medication query - provide balanced response
      response = `I understand you have questions about medications. Let me explain how I can help:\n\n**My Role:**\nI'm a clinical decision-support tool and medical intake assistant. I help assess symptoms, perform triage evaluations, and gather medical information.\n\n**What I CAN do:**\n• Assess your symptoms and determine care urgency (triage)\n• Conduct a medical interview to gather information\n• Generate a clinical summary for your doctor\n• Help you prepare for your healthcare visit\n\n**What I CANNOT do:**\n• Prescribe or recommend specific medications\n• Diagnose conditions\n• Replace professional medical advice\n\n**How can I help you today?**\n• If you want to check medication interactions → Use "Check Medications" in the menu\n• If you have symptoms to assess → Describe them and I'll perform a triage assessment\n• If you want a medical interview → I can guide you through that process\n\nWhat would you like to do?`
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response,
        timestamp: new Date()
      }])
    }
  }

  const performTriage = async (symptomsText) => {
    try {
      const response = await interviewAPI.triage({ text: symptomsText })
      const triageLevel = response.data.triage
      const triageMsg = response.data.message || `Triage assessment complete. Priority level: ${triageLevel}`
      
      setTriageDone(true)
      setTriageLevel(triageLevel)
      setTriageMessage(triageMsg)
      
      // Check if we need to skip interview (VERY_URGENT or IMMEDIATE)
      if (triageLevel === 'VERY_URGENT' || triageLevel === 'IMMEDIATE') {
        // For urgent cases: Display triage immediately, then SOAP
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `**🚨 URGENT ASSESSMENT**\n\n${triageMsg}\n\n**Priority Level:** ${triageLevel}`,
          timestamp: new Date(),
          triageLevel: triageLevel
        }])
        // Skip interview, go directly to SOAP generation
        await generateSOAPDirectly(symptomsText, triageLevel)
      } else {
        // For STANDARD and URGENT: Don't display triage yet, just start interview
        // Triage will be shown after SOAP
        await startInterview()
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to perform triage assessment.')
      console.error('Triage error:', err)
    }
  }

  const startInterview = async () => {
    try {
      setInterviewInProgress(true)
      const response = await interviewAPI.startInterview({ language: 'English' })
      const sessionId = response.data.session_id
      const firstQuestion = response.data.agent_message
      
      setInterviewSessionId(sessionId)
      setCurrentQuestion(firstQuestion)
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `**Starting Patient Interview**\n\n${firstQuestion}`,
        timestamp: new Date()
      }])
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start interview.')
      console.error('Start interview error:', err)
      setInterviewInProgress(false)
    }
  }

  const submitInterviewAnswer = async (answer) => {
    if (!interviewSessionId) return

    setLoading(true)
    try {
      const response = await interviewAPI.submitAnswer({
        session_id: interviewSessionId,
        answer: answer
      })

      if (response.data.next_step === 'generate_summary') {
        // Interview complete, generate SOAP
        await generateSOAP()
      } else if (response.data.next_question) {
        // Continue interview
        setCurrentQuestion(response.data.next_question)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: response.data.next_question,
          timestamp: new Date()
        }])
      } else if (response.data.message) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: response.data.message,
          timestamp: new Date()
        }])
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit answer.')
      console.error('Submit answer error:', err)
    } finally {
      setLoading(false)
    }
  }

  const stopInterviewEarly = async () => {
    if (!interviewSessionId || !interviewInProgress) return
    
    // Add a message indicating interview was stopped early
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: 'Interview stopped early. Generating summary with collected information...',
      timestamp: new Date()
    }])
    
    // Generate SOAP with current interview data
    await generateSOAP()
  }

  const generateSOAP = async () => {
    if (!interviewSessionId) return

    setLoading(true)
    try {
      const response = await interviewAPI.generateSummary({
        session_id: interviewSessionId
      })
      
      setSoapNote(response.data.soap_note)
      setSoapPdfUrl(response.data.pdf_url)
      setInterviewInProgress(false)
      
      // Capture triage info before async operations
      const currentTriageLevel = triageLevel
      const currentTriageMessage = triageMessage
      
      // Display SOAP note first (without triage)
      const soapContent = `**Clinical Summary (SOAP Note)**\n\n${response.data.soap_note}`
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: soapContent,
        timestamp: new Date(),
        soapNote: response.data.soap_note,
        triageLevel: currentTriageLevel,
        pdfUrl: response.data.pdf_url
      }])
      
      // Then display triage response after SOAP (for STANDARD and URGENT)
      // Check if triage level is STANDARD or URGENT (not VERY_URGENT or IMMEDIATE)
      if (currentTriageLevel && currentTriageLevel !== 'VERY_URGENT' && currentTriageLevel !== 'IMMEDIATE') {
        // Use a small delay to show SOAP first, then triage
        setTimeout(() => {
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: `**Triage Assessment**\n\n${currentTriageMessage || 'Triage assessment complete.'}\n\n**Priority Level:** ${currentTriageLevel}`,
            timestamp: new Date(),
            triageLevel: currentTriageLevel
          }])
        }, 800) // Small delay to show SOAP first
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate SOAP note.')
      console.error('Generate SOAP error:', err)
    } finally {
      setLoading(false)
    }
  }

  const generateSOAPDirectly = async (symptomsText, triageLevelValue) => {
    setLoading(true)
    try {
      // For urgent cases, we still need to create a minimal interview session
      // Start interview, immediately generate summary
      const startResponse = await interviewAPI.startInterview({ language: 'English' })
      const sessionId = startResponse.data.session_id
      
      // Submit symptoms as first answer
      await interviewAPI.submitAnswer({
        session_id: sessionId,
        answer: symptomsText
      })
      
      // Generate SOAP immediately
      const response = await interviewAPI.generateSummary({
        session_id: sessionId
      })
      
      setSoapNote(response.data.soap_note)
      setSoapPdfUrl(response.data.pdf_url)
      
      // Display triage and SOAP
      const soapContent = `**🚨 URGENT ASSESSMENT**\n\n**Triage Level:** ${triageLevelValue}\n**Triage Assessment:** ${triageMessage}\n\n**Clinical Summary (SOAP Note)**\n\n${response.data.soap_note}`
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: soapContent,
        timestamp: new Date(),
        soapNote: response.data.soap_note,
        triageLevel: triageLevelValue,
        pdfUrl: response.data.pdf_url
      }])
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate SOAP note.')
      console.error('Generate SOAP error:', err)
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim() || loading) return

    const userMessage = searchQuery.trim()
    setSearchQuery('')
    setError(null)

    setLoading(true)

    try {
      // Check for medication/prescription queries FIRST (before triage/interview flow)
      if (isMedicationQuery(userMessage)) {
        await handleMedicationQuery(userMessage)
        setLoading(false)
        inputRef.current?.focus()
        return
      }

      // Check if assessment is complete and user wants to start new conversation
      const isAssessmentComplete = triageDone && !interviewInProgress && soapNote
      
      if (isAssessmentComplete) {
        // User is starting a new conversation after previous assessment
        // Reset state first
        stopSpeaking()
        setTriageDone(false)
        setTriageLevel(null)
        setTriageMessage(null)
        setInterviewSessionId(null)
        setCurrentQuestion(null)
        setInterviewInProgress(false)
        setSoapNote(null)
        setSoapPdfUrl(null)
        
        // Clear messages and show initial greeting
        setMessages([{
          role: 'assistant',
          content: "Hello! I'm here to help assess your medical situation. Please describe your symptoms or concerns, and I'll perform a triage assessment to determine the appropriate care pathway.",
          timestamp: new Date()
        }])
        
        // Add user message
        setMessages(prev => [...prev, {
          role: 'user',
          content: userMessage,
          timestamp: new Date()
        }])
        
        // Perform triage on the new message
        await performTriage(userMessage)
        return
      }

      // Add user message to UI immediately
      setMessages(prev => [...prev, {
        role: 'user',
        content: userMessage,
        timestamp: new Date()
      }])

      if (!triageDone) {
        // First message: Perform triage
        await performTriage(userMessage)
      } else if (interviewInProgress && currentQuestion) {
        // Interview in progress: Submit answer
        await submitInterviewAnswer(userMessage)
      } else {
        // Assessment complete - allow starting new conversation
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: "I've completed the assessment. You can start a new conversation by typing your symptoms or concerns below, or click 'Start New Conversation' button above.",
          timestamp: new Date()
        }])
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to process message. Please try again.')
      console.error('Send message error:', err)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleInputFocus = () => {
    setIsFocused(true)
    if (!conversationMode) {
      setConversationMode(true)
    }
  }

  const handleInputClick = () => {
    if (!conversationMode) {
      setConversationMode(true)
    }
  }

  const startNewConversation = () => {
    stopSpeaking()
    setSearchQuery('')
    setMessages([])
    setError(null)
    // Reset flow state
    setTriageDone(false)
    setTriageLevel(null)
    setTriageMessage(null)
    setInterviewSessionId(null)
    setCurrentQuestion(null)
    setInterviewInProgress(false)
    setSoapNote(null)
    setSoapPdfUrl(null)
    
    // Show initial greeting for new conversation
    setMessages([{
      role: 'assistant',
      content: "Hello! I'm here to help assess your medical situation. Please describe your symptoms or concerns, and I'll perform a triage assessment to determine the appropriate care pathway.",
      timestamp: new Date()
    }])
    
    // Focus input
    setTimeout(() => {
      inputRef.current?.focus()
    }, 100)
  }

  const exitConversationMode = () => {
    stopSpeaking()
    setConversationMode(false)
    setSearchQuery('')
    setMessages([])
    setError(null)
    // Reset flow state
    setTriageDone(false)
    setTriageLevel(null)
    setTriageMessage(null)
    setInterviewSessionId(null)
    setCurrentQuestion(null)
    setInterviewInProgress(false)
    setSoapNote(null)
    setSoapPdfUrl(null)
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

  // Conversation Mode - Full screen chat interface
  if (conversationMode) {
    return (
      <div className="h-screen bg-white flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#e2e8f0] flex-shrink-0">
          <div className="flex items-center gap-3">
            <div>
              <h2 className="font-semibold text-[#1a1a1a]">MedAI Assistant</h2>
              <p className="text-xs text-[#4a5568]">
                {triageDone ? (interviewInProgress ? 'Interview in progress' : 'Assessment complete') : 'Starting assessment...'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleVoice}
              className={`p-2 rounded-full transition-colors ${
                voiceEnabled
                  ? 'hover:bg-[#f7fafc] text-[#4285f4]'
                  : 'hover:bg-[#f7fafc] text-[#718096]'
              }`}
              title={voiceEnabled ? 'Disable voice' : 'Enable voice'}
            >
              {voiceEnabled ? (
                <Volume2 className="w-5 h-5" />
              ) : (
                <VolumeX className="w-5 h-5" />
              )}
            </button>
            {isSpeaking && (
              <div className="flex items-center gap-1 text-[#4285f4] text-xs">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Speaking...</span>
              </div>
            )}
            <button
              onClick={exitConversationMode}
              className="p-2 rounded-full hover:bg-[#f7fafc] transition-colors"
              title="Exit conversation"
            >
              <X className="w-5 h-5 text-[#4a5568]" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-[#4285f4] text-white'
                    : 'bg-[#f7fafc] text-[#1a1a1a] border border-[#e2e8f0]'
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
                {msg.urgency && (
                  <div className={`mt-2 pt-2 border-t ${
                    msg.urgency === 'IMMEDIATE' ? 'border-red-300' :
                    msg.urgency === 'VERY_URGENT' ? 'border-orange-300' :
                    'border-[#e2e8f0]'
                  }`}>
                    <p className={`text-xs font-medium ${
                      msg.urgency === 'IMMEDIATE' ? 'text-red-700' :
                      msg.urgency === 'VERY_URGENT' ? 'text-orange-700' :
                      'text-[#4a5568]'
                    }`}>
                      Urgency Level: <span className="font-bold">{msg.urgency}</span>
                    </p>
                  </div>
                )}
                {msg.action_required && (
                  <div className="mt-2 pt-2 border-t border-red-300 bg-red-50 rounded p-2">
                    <p className="text-sm font-bold text-red-800">
                      ⚠️ {msg.action_required}
                    </p>
                  </div>
                )}
                {msg.suggested_workflow && (
                  <div className="mt-2 pt-2 border-t border-[#e2e8f0]">
                    <p className="text-xs text-[#4a5568]">
                      Suggested workflow: <span className="font-medium">{msg.suggested_workflow}</span>
                    </p>
                  </div>
                )}
                {msg.pdfUrl && (
                  <div className="mt-3 pt-3 border-t border-[#e2e8f0]">
                    <a
                      href={`http://localhost:8000${msg.pdfUrl}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      className="inline-flex items-center gap-2 px-3 py-2 bg-[#4285f4] text-white rounded-lg hover:bg-[#1967d2] transition-colors text-sm font-medium"
                    >
                      <FileText className="w-4 h-4" />
                      Download PDF Report
                    </a>
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
              <div className="bg-[#f7fafc] rounded-2xl px-4 py-3 border border-[#e2e8f0]">
                <Loader2 className="w-5 h-5 text-[#4285f4] animate-spin" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="px-4 pb-2 flex-shrink-0">
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-[#e2e8f0] bg-white flex-shrink-0">
          <form onSubmit={sendMessage} className="max-w-4xl mx-auto">
            {/* Stop Interview Button - Only show when agent is idle (waiting for answer) */}
            {interviewInProgress && !loading && currentQuestion && messages.length > 0 && (
              <div className="mb-3 flex justify-center">
                <button
                  type="button"
                  onClick={stopInterviewEarly}
                  disabled={loading}
                  className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition-colors text-sm font-medium disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 shadow-md hover:shadow-lg"
                  title="Stop interview and generate summary / انٹرویو روکیں اور خلاصہ بنائیں / Interview Roken"
                >
                  <Square className="w-4 h-4" />
                  <span>Stop Interview / انٹرویو روکیں</span>
                </button>
              </div>
            )}
            
            {/* Start New Conversation Button - Show when assessment is complete */}
            {triageDone && !interviewInProgress && soapNote && !loading && (
              <div className="mb-3 flex justify-center">
                <button
                  type="button"
                  onClick={startNewConversation}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors text-sm font-medium flex items-center gap-2 shadow-md hover:shadow-lg"
                  title="Start a new conversation / نیا گفتگو شروع کریں"
                >
                  <MessageSquare className="w-4 h-4" />
                  <span>Start New Conversation / نیا گفتگو شروع کریں</span>
                </button>
              </div>
            )}
            
            <div className="relative flex items-center w-full h-14 px-5 rounded-full border border-[#e2e8f0] bg-white shadow-sm hover:shadow-md transition-all">
              <Search className="w-5 h-5 text-[#718096] mr-3 flex-shrink-0" />
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={
                  !triageDone 
                    ? "Describe your symptoms..." 
                    : interviewInProgress 
                    ? "Answer the question..." 
                    : (soapNote ? "Start a new conversation - describe symptoms..." : "Type your message...")
                }
                className="flex-1 outline-none text-[#1a1a1a] text-base bg-transparent placeholder-[#718096]"
                disabled={loading || isListening}
              />
              <button
                type="button"
                onClick={toggleListening}
                disabled={loading || isListening}
                className={`ml-2 p-2 rounded-full transition-colors ${
                  isListening
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'bg-gray-100 hover:bg-gray-200 text-[#4a5568]'
                } disabled:bg-gray-200 disabled:cursor-not-allowed`}
                title={isListening ? "Listening... Click to stop" : "Start voice input / آواز سے لکھیں"}
              >
                <Mic className="w-5 h-5" />
              </button>
              <button
                type="submit"
                disabled={loading || !searchQuery.trim() || isListening}
                className="ml-2 px-4 py-2 bg-[#4285f4] text-white rounded-full hover:bg-[#1967d2] disabled:bg-[#a0aec0] disabled:cursor-not-allowed flex items-center gap-2 transition-colors font-medium"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
            {isListening && (
              <div className="mt-2 flex items-center justify-center gap-2 text-sm text-[#4285f4]">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span>Listening... / سن رہا ہوں</span>
              </div>
            )}
            <p className="text-xs text-[#718096] mt-2 text-center">
              Powered by MedAI • Triage Assessment & Patient Interview
            </p>
          </form>
        </div>
      </div>
    )
  }

  // Normal Home Page Mode
  return (
    <div className="relative flex flex-col h-full bg-white">
      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-24">
        <div className="flex flex-col items-center justify-center min-h-full py-8">
          {/* Title */}
          <div className="mb-12 mt-8">
            <h1 className="text-7xl md:text-8xl font-semibold text-[#1a1a1a] text-center mb-4 tracking-tighter">
              Med<span className="text-[#4285f4] font-semibold">AI</span>
            </h1>
            <p className="text-xl text-[#4a5568] text-center font-normal">
              Your medical AI assistant
            </p>
          </div>

          {/* Quick Action Chips */}
          <div className="w-full max-w-2xl mb-12">
            <div className="flex flex-wrap justify-center gap-3">
              {quickActions.map((action) => {
                const Icon = action.icon
                return (
                  <button
                    key={action.path}
                    onClick={() => navigate(action.path)}
                    className="flex items-center gap-2 px-5 py-2.5 bg-white hover:bg-[#f7fafc] border border-[#e2e8f0] rounded-full text-sm text-[#1a1a1a] transition-all hover:shadow-sm font-medium"
                  >
                    <Icon className="w-4 h-4" />
                    <span>{action.title}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Feature Cards */}
          <div className="w-full max-w-5xl mt-8 mb-8">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {quickActions.map((action) => {
                const Icon = action.icon
                return (
                  <div
                    key={action.path}
                    onClick={() => navigate(action.path)}
                    className="group cursor-pointer p-8 rounded-2xl border border-[#e2e8f0] hover:border-[#4285f4] hover:shadow-lg transition-all bg-white hover:bg-[#f7fafc]"
                  >
                    <div className="w-14 h-14 rounded-full bg-[#e8f0fe] flex items-center justify-center mb-5 group-hover:bg-[#d2e3fc] group-hover:scale-110 transition-all">
                      <Icon className="w-7 h-7 text-[#1967d2]" />
                    </div>
                    <h3 className="text-xl font-semibold text-[#1a1a1a] mb-2">
                      {action.title}
                    </h3>
                    <p className="text-sm text-[#4a5568] leading-relaxed">
                      {action.description}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Footer Note */}
          <div className="mt-auto mb-8 text-center">
            <p className="text-xs text-[#4a5568]">
              Medical AI Assistant • Lab Analysis • Patient Interviews • Medication Safety
            </p>
          </div>
        </div>
      </div>

      {/* Fixed Search Box at Bottom - Gemini Style */}
      <div className="fixed bottom-0 left-0 right-0 py-4 px-4 z-10">
        <div className="max-w-2xl mx-auto">
          <form onSubmit={(e) => { e.preventDefault(); handleInputClick(); }}>
            <div
              className={`relative flex items-center w-full h-14 px-5 rounded-full border transition-all duration-200 bg-white ${
                isFocused
                  ? 'shadow-md border-[#4285f4]'
                  : 'shadow-sm border-[#e2e8f0] hover:shadow-md hover:border-[#cbd5e0]'
              }`}
            >
              <Search className="w-5 h-5 text-[#718096] mr-3 flex-shrink-0" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={handleInputFocus}
                onClick={handleInputClick}
                onBlur={() => setIsFocused(false)}
                placeholder="Ask anything about medical analysis... (Click to start conversation)"
                className="flex-1 outline-none text-[#1a1a1a] text-base bg-transparent placeholder-[#718096] cursor-text"
              />
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
