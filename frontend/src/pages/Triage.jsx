import { useState } from 'react'
import { Activity, Loader2, AlertTriangle } from 'lucide-react'
import { interviewAPI } from '../services/api'

export default function Triage() {
  const [triageSymptoms, setTriageSymptoms] = useState('')
  const [triageLoading, setTriageLoading] = useState(false)
  const [triageError, setTriageError] = useState(null)
  const [triageResult, setTriageResult] = useState(null)

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

  return (
    <div className="px-4 py-8 min-h-screen bg-white dark:bg-[#1a1a1a]">
      <div className="max-w-4xl mx-auto">
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

            {/* Info Section */}
            <div className="mt-12 max-w-2xl w-full">
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl p-6">
                <div className="flex items-start">
                  <AlertTriangle className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">About Triage Levels</h3>
                    <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-2">
                      <li className="flex items-start">
                        <span className="font-semibold mr-2">IMMEDIATE:</span>
                        <span>Life-threatening conditions requiring immediate medical attention</span>
                      </li>
                      <li className="flex items-start">
                        <span className="font-semibold mr-2">VERY_URGENT:</span>
                        <span>Serious conditions requiring urgent care within hours</span>
                      </li>
                      <li className="flex items-start">
                        <span className="font-semibold mr-2">URGENT:</span>
                        <span>Conditions requiring prompt medical attention</span>
                      </li>
                      <li className="flex items-start">
                        <span className="font-semibold mr-2">STANDARD:</span>
                        <span>Non-urgent conditions that can be addressed during regular hours</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
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

              {/* Action Button */}
              <button
                onClick={() => {
                  setTriageResult(null)
                  setTriageSymptoms('')
                  setTriageError(null)
                }}
                className="w-full bg-[#4285f4] dark:bg-[#1a73e8] text-white py-3 px-6 rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] transition-colors font-medium shadow-md hover:shadow-lg"
              >
                New Assessment
              </button>

              {/* Info Section */}
              <div className="mt-8">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl p-6">
                  <div className="flex items-start">
                    <AlertTriangle className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">About Triage Levels</h3>
                      <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-2">
                        <li className="flex items-start">
                          <span className="font-semibold mr-2">IMMEDIATE:</span>
                          <span>Life-threatening conditions requiring immediate medical attention</span>
                        </li>
                        <li className="flex items-start">
                          <span className="font-semibold mr-2">VERY_URGENT:</span>
                          <span>Serious conditions requiring urgent care within hours</span>
                        </li>
                        <li className="flex items-start">
                          <span className="font-semibold mr-2">URGENT:</span>
                          <span>Conditions requiring prompt medical attention</span>
                        </li>
                        <li className="flex items-start">
                          <span className="font-semibold mr-2">STANDARD:</span>
                          <span>Non-urgent conditions that can be addressed during regular hours</span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
