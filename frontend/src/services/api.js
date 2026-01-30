import axios from 'axios'

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Lab Analyzer API (Hassan)
export const labAnalyzerAPI = {
  uploadReport: (formData) => {
    return api.post('/api/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  getStatus: (reportId) => {
    return api.get(`/status/${reportId}/api/`)
  },
  getResults: (reportId) => {
    return api.get(`/api/results/${reportId}/`)
  },
  downloadPDF: (reportId) => {
    return api.get(`/results/${reportId}/download/`, {
      responseType: 'blob',
    })
  },
}

// Interview API (Abdullah)
export const interviewAPI = {
  startInterview: (data) => {
    return api.post('/medai/interview/start/', data)
  },
  submitAnswer: (data) => {
    return api.post('/medai/interview/answer/', data)
  },
  generateSummary: (data) => {
    return api.post('/medai/interview/summary/', data)
  },
  triage: (data) => {
    return api.post('/medai/interview/triage/', data)
  },
}

// Medication Interaction API (Faizan)
export const medicationAPI = {
  analyzeInteraction: (data) => {
    return api.post('/medai/medication_interaction/analyze_interaction/', data)
  },
}

// Orchestrator Conversation API
export const conversationAPI = {
  startConversation: (data) => {
    return api.post('/medai/conversation/start/', data)
  },
  continueConversation: (data) => {
    return api.post('/medai/conversation/continue/', data)
  },
  getHistory: (sessionId) => {
    return api.get(`/medai/conversation/${sessionId}/`)
  },
}

// Orchestrator Workflow API
export const workflowAPI = {
  suggestWorkflow: (context) => {
    return api.post('/medai/workflow/suggest/', context)
  },
  executeWorkflow: (data) => {
    return api.post('/medai/workflow/execute/', data)
  },
  comprehensiveCare: (data) => {
    return api.post('/medai/workflow/comprehensive/', data)
  },
}

export default api
