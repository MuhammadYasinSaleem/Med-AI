import { useState, useEffect } from 'react'
import { Upload, FileText, Loader2, CheckCircle, AlertCircle, Download, AlertTriangle } from 'lucide-react'
import { labAnalyzerAPI } from '../services/api'

export default function LabAnalyzer() {
  const [formData, setFormData] = useState({
    patient_name: '',
    age: '',
    gender: 'M',
    preferred_language: 'en',
    is_pregnant: false,
    contact: '',
    file: null,
  })
  const [uploading, setUploading] = useState(false)
  const [reportId, setReportId] = useState(null)
  const [status, setStatus] = useState(null)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [polling, setPolling] = useState(false)

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      // Check file size (10MB limit)
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('File size exceeds 10MB limit')
        return
      }
      // Check file type
      const ext = selectedFile.name.split('.').pop().toLowerCase()
      if (!['pdf', 'jpg', 'jpeg', 'png'].includes(ext)) {
        setError('Invalid file type. Allowed: PDF, JPG, JPEG, PNG')
        return
      }
      setFormData(prev => ({ ...prev, file: selectedFile }))
      setError(null)
      setResults(null)
    }
  }

  // Poll status when report is processing
  useEffect(() => {
    let intervalId
    if (polling && reportId) {
      intervalId = setInterval(async () => {
        try {
          const response = await labAnalyzerAPI.getStatus(reportId)
          setStatus(response.data)
          
          if (response.data.status === 'completed' && response.data.has_analysis) {
            setPolling(false)
            await fetchResults(reportId)
          } else if (response.data.status === 'failed') {
            setPolling(false)
            setError(response.data.error_message || 'Analysis failed')
          }
        } catch (err) {
          console.error('Status check error:', err)
        }
      }, 2000) // Poll every 2 seconds
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [polling, reportId])

  const fetchResults = async (id) => {
    try {
      const response = await labAnalyzerAPI.getResults(id)
      if (response.data.success) {
        setResults(response.data)
        setPolling(false)
        setUploading(false)
      } else {
        // If not ready yet, continue polling
        if (response.status === 202) {
          setStatus({ status: 'processing', has_analysis: false })
        } else {
          setError(response.data.error || 'Failed to fetch results')
        }
      }
    } catch (err) {
      if (err.response?.status === 202) {
        // Analysis not ready yet, continue polling
        setStatus({ status: 'processing', has_analysis: false })
      } else {
        setError(err.response?.data?.error || 'Failed to fetch results')
        setPolling(false)
      }
    }
  }

  const handleUpload = async () => {
    // Validation
    if (!formData.patient_name.trim()) {
      setError('Please enter patient name')
      return
    }
    if (!formData.age || formData.age < 0 || formData.age > 150) {
      setError('Please enter a valid age (0-150)')
      return
    }
    if (!formData.file) {
      setError('Please select a file to upload')
      return
    }

    setUploading(true)
    setError(null)
    setResults(null)
    setStatus(null)

    try {
      const uploadFormData = new FormData()
      uploadFormData.append('patient_name', formData.patient_name)
      uploadFormData.append('age', formData.age)
      uploadFormData.append('gender', formData.gender)
      uploadFormData.append('preferred_language', formData.preferred_language)
      uploadFormData.append('is_pregnant', formData.is_pregnant)
      uploadFormData.append('contact', formData.contact || '')
      uploadFormData.append('file', formData.file)

      const response = await labAnalyzerAPI.uploadReport(uploadFormData)
      
      // Handle API response
      if (response.data.success && response.data.report_id) {
        const id = response.data.report_id
        setReportId(id)
        setUploading(false)
        
        // If already completed, fetch results directly
        if (response.data.status === 'completed') {
          await fetchResults(id)
        } else {
          // Otherwise start polling
          setPolling(true)
          // Initial status check
          const statusResponse = await labAnalyzerAPI.getStatus(id)
          setStatus(statusResponse.data)
          
          if (statusResponse.data.status === 'completed' && statusResponse.data.has_analysis) {
            await fetchResults(id)
          }
        }
      } else {
        setError('Invalid response from server')
        setUploading(false)
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to upload report')
      setUploading(false)
      setPolling(false)
    }
  }

  const handleDownloadPDF = async () => {
    if (!reportId) return
    
    try {
      const response = await labAnalyzerAPI.downloadPDF(reportId)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `lab_report_summary_${reportId}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Failed to download PDF')
    }
  }

  return (
    <div className="px-4 py-8 min-h-screen bg-white dark:bg-[#1a1a1a]">
      <div className="max-w-4xl mx-auto">
        {/* Patient Information Form - Gemini Style */}
        {!results && (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-semibold text-[#202124] dark:text-[#e8eaed] mb-2">Lab Report Analyzer</h2>
              <p className="text-[#5f6368] dark:text-[#9aa0a6]">
                Upload and analyze lab reports with AI-powered insights
              </p>
            </div>
            
            <div className="w-full max-w-2xl space-y-6">
              <div className="bg-white dark:bg-[#303134] rounded-2xl shadow-lg p-8 border border-[#e2e8f0] dark:border-[#5f6368] transition-colors">
                <h3 className="text-xl font-semibold text-[#202124] dark:text-[#e8eaed] mb-6">Patient Information</h3>
                
                <div className="space-y-4 mb-6">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-2">
                        Patient Name *
                      </label>
                      <input
                        type="text"
                        name="patient_name"
                        value={formData.patient_name}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md placeholder-[#9aa0a6] dark:placeholder-[#5f6368]"
                        placeholder="Enter patient name"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-2">
                        Age *
                      </label>
                      <input
                        type="number"
                        name="age"
                        value={formData.age}
                        onChange={handleInputChange}
                        min="0"
                        max="150"
                        className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md placeholder-[#9aa0a6] dark:placeholder-[#5f6368]"
                        placeholder="Age in years"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-2">
                        Gender *
                      </label>
                      <select
                        name="gender"
                        value={formData.gender}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md"
                      >
                        <option value="M">Male</option>
                        <option value="F">Female</option>
                        <option value="O">Other</option>
                        <option value="U">Unknown</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-2">
                        Preferred Language *
                      </label>
                      <select
                        name="preferred_language"
                        value={formData.preferred_language}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md"
                      >
                        <option value="en">English</option>
                        <option value="ur">Urdu (اردو)</option>
                        <option value="pa">Punjabi (ਪੰਜਾਬੀ)</option>
                        <option value="ps">Pashto (پښتو)</option>
                        <option value="sd">Sindhi (سنڌي)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-2">
                        Contact (Optional)
                      </label>
                      <input
                        type="text"
                        name="contact"
                        value={formData.contact}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md placeholder-[#9aa0a6] dark:placeholder-[#5f6368]"
                        placeholder="Contact information"
                      />
                    </div>

                    <div className="flex items-center pt-8">
                      <input
                        type="checkbox"
                        name="is_pregnant"
                        checked={formData.is_pregnant}
                        onChange={handleInputChange}
                        className="w-4 h-4 text-[#4285f4] dark:text-[#8ab4f8] border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] rounded focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8]"
                      />
                      <label className="ml-2 text-sm text-[#5f6368] dark:text-[#9aa0a6]">
                        Is Patient Pregnant?
                      </label>
                    </div>
                  </div>
                </div>

                {/* File Upload */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-3">
                    Lab Report File *
                  </label>
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-[#dfe1e5] dark:border-[#5f6368] border-dashed rounded-2xl hover:border-[#4285f4] dark:hover:border-[#8ab4f8] transition-colors bg-[#f8f9fa] dark:bg-[#202124]">
                    <div className="space-y-1 text-center">
                      <Upload className="mx-auto h-12 w-12 text-[#9aa0a6] dark:text-[#5f6368]" />
                      <div className="flex text-sm text-[#5f6368] dark:text-[#9aa0a6]">
                        <label className="relative cursor-pointer rounded-md font-medium text-[#4285f4] dark:text-[#8ab4f8] hover:text-[#1967d2] dark:hover:text-[#1557b0]">
                          <span>Upload a file</span>
                          <input
                            type="file"
                            className="sr-only"
                            accept=".pdf,.jpg,.jpeg,.png"
                            onChange={handleFileChange}
                          />
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className="text-xs text-[#9aa0a6] dark:text-[#5f6368]">PDF, JPG, JPEG, PNG up to 10MB</p>
                      {formData.file && (
                        <p className="text-sm text-[#202124] dark:text-[#e8eaed] mt-2">
                          Selected: <span className="font-medium">{formData.file.name}</span>
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleUpload}
                  disabled={!formData.file || uploading || polling}
                  className="w-full bg-[#4285f4] dark:bg-[#1a73e8] text-white py-4 px-6 rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] disabled:bg-[#9aa0a6] disabled:cursor-not-allowed flex items-center justify-center transition-colors font-medium shadow-md hover:shadow-lg text-base"
                >
                  {uploading || polling ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      {polling ? 'Processing...' : 'Uploading...'}
                    </>
                  ) : (
                    <>
                      <FileText className="w-5 h-5 mr-2" />
                      Analyze Report
                    </>
                  )}
                </button>
              </div>

              {/* Error Display */}
              {error && (
                <div className="max-w-2xl w-full bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-4">
                  <div className="flex items-start">
                    <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-medium text-red-800 dark:text-red-400">Error</h3>
                      <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Status Display */}
              {status && !results && (
                <div className="max-w-2xl w-full bg-white dark:bg-[#303134] rounded-2xl shadow-lg p-6 border border-[#e2e8f0] dark:border-[#5f6368] transition-colors">
                  <div className="flex items-center mb-4">
                    <Loader2 className="w-6 h-6 text-[#4285f4] dark:text-[#8ab4f8] mr-2 animate-spin" />
                    <h2 className="text-xl font-semibold text-[#202124] dark:text-[#e8eaed]">Processing Status</h2>
                  </div>
                  <div className="space-y-2">
                    <p className="text-[#5f6368] dark:text-[#9aa0a6]">
                      Status: <span className="font-medium text-[#202124] dark:text-[#e8eaed]">{status.status}</span>
                    </p>
                    {status.critical_count > 0 && (
                      <p className="text-red-600 dark:text-red-400 font-medium">
                        Critical Findings: {status.critical_count}
                      </p>
                    )}
                    {status.error_message && (
                      <p className="text-red-600 dark:text-red-400">{status.error_message}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Display (when results exist) */}
        {error && results && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-4">
            <div className="flex items-start">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-red-800 dark:text-red-400">Error</h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Results Display - Gemini Style */}
        {results && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] py-8">
            <div className="w-full max-w-4xl space-y-6">
              {/* Result Header */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#e8f0fe] dark:bg-[#303134] mb-4">
                  <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                </div>
                <h2 className="text-3xl font-semibold text-[#202124] dark:text-[#e8eaed] mb-2">Analysis Complete</h2>
                <p className="text-[#5f6368] dark:text-[#9aa0a6]">Lab report analysis results</p>
              </div>

              {/* Result Card */}
              <div className="bg-white dark:bg-[#303134] rounded-2xl shadow-lg p-8 border border-[#e2e8f0] dark:border-[#5f6368]">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-semibold text-[#202124] dark:text-[#e8eaed]">Analysis Results</h3>
                  <button
                    onClick={handleDownloadPDF}
                    className="flex items-center gap-2 px-4 py-2 bg-[#4285f4] dark:bg-[#1a73e8] text-white rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] transition-colors font-medium shadow-md hover:shadow-lg"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </button>
                </div>
                
                <div className="space-y-6">
                  {/* Patient Info */}
                  {results.lab_report && (
                    <div className="p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                      <h3 className="font-semibold text-[#202124] dark:text-[#e8eaed] mb-3">Patient Information</h3>
                      <div className="grid md:grid-cols-2 gap-3 text-sm text-[#5f6368] dark:text-[#9aa0a6]">
                        <p><span className="font-medium text-[#202124] dark:text-[#e8eaed]">Name:</span> {results.lab_report.patient?.name}</p>
                        <p><span className="font-medium text-[#202124] dark:text-[#e8eaed]">Age:</span> {results.lab_report.patient?.age} years</p>
                        <p><span className="font-medium text-[#202124] dark:text-[#e8eaed]">Gender:</span> {results.lab_report.patient?.gender}</p>
                        <p><span className="font-medium text-[#202124] dark:text-[#e8eaed]">Language:</span> {results.lab_report.patient?.preferred_language}</p>
                      </div>
                    </div>
                  )}

                  {/* Humanistic Summary */}
                  {results.humanistic_summary && (
                    <div className="p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                      <h3 className="font-semibold text-[#202124] dark:text-[#e8eaed] mb-3">Summary</h3>
                      <p className="text-[#202124] dark:text-[#e8eaed] whitespace-pre-wrap leading-relaxed">
                        {results.humanistic_summary}
                      </p>
                    </div>
                  )}

                  {/* Critical Findings */}
                  {results.critical_findings && results.critical_findings.length > 0 && (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-6 transition-colors">
                      <div className="flex items-center mb-4">
                        <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2" />
                        <h3 className="font-semibold text-red-800 dark:text-red-400">
                          Critical Findings ({results.critical_findings.length})
                        </h3>
                      </div>
                      <div className="space-y-4">
                        {results.critical_findings.map((finding, idx) => (
                          <div key={idx} className="bg-white dark:bg-[#202124] rounded-xl p-4 transition-colors border border-red-200 dark:border-red-800">
                            <p className="font-medium text-red-800 dark:text-red-400">
                              {finding.test}: {finding.value} (Range: {finding.reference_range})
                            </p>
                            <p className="text-sm text-red-700 dark:text-red-300 mt-1">{finding.explanation}</p>
                            {finding.immediate_actions && finding.immediate_actions.length > 0 && (
                              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                                Actions: {finding.immediate_actions.join(', ')}
                              </p>
                            )}
                            {finding.time_sensitivity && (
                              <p className="text-sm font-medium text-red-800 dark:text-red-400 mt-1">
                                Urgency: {finding.time_sensitivity}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Abnormal Findings */}
                  {results.abnormal_findings && results.abnormal_findings.length > 0 && (
                    <div className="p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                      <h3 className="font-semibold text-[#202124] dark:text-[#e8eaed] mb-4">
                        Abnormal Findings ({results.abnormal_findings.length})
                      </h3>
                      <div className="space-y-3">
                        {results.abnormal_findings.map((finding, idx) => (
                          <div key={idx} className="border-l-4 border-orange-400 dark:border-orange-600 pl-4 py-2 bg-orange-50 dark:bg-orange-900/10 rounded-r-lg">
                            <p className="font-medium text-[#202124] dark:text-[#e8eaed]">
                              {finding.test}: {finding.value} ({finding.severity}) - Range: {finding.reference_range}
                            </p>
                            <p className="text-sm text-[#5f6368] dark:text-[#9aa0a6] mt-1">{finding.explanation}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Normal Findings */}
                  {results.normal_findings && results.normal_findings.length > 0 && (
                    <div className="p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                      <h3 className="font-semibold text-[#202124] dark:text-[#e8eaed]">
                        Normal Findings: {results.normal_findings.length} tests within normal range
                      </h3>
                    </div>
                  )}

                  {/* SOAP Note */}
                  {results.soap_note && (
                    <div className="p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                      <h3 className="font-semibold text-[#202124] dark:text-[#e8eaed] mb-4">Clinical Summary (SOAP)</h3>
                      <div className="space-y-4">
                        {results.soap_note.subjective && (
                          <div className="bg-blue-50 dark:bg-blue-900/10 rounded-lg p-4 border-l-4 border-blue-500">
                            <p className="font-medium text-blue-700 dark:text-blue-400 mb-1">Subjective:</p>
                            <p className="text-[#5f6368] dark:text-[#9aa0a6] whitespace-pre-wrap">{results.soap_note.subjective}</p>
                          </div>
                        )}
                        {results.soap_note.objective && (
                          <div className="bg-green-50 dark:bg-green-900/10 rounded-lg p-4 border-l-4 border-green-500">
                            <p className="font-medium text-green-700 dark:text-green-400 mb-1">Objective:</p>
                            <p className="text-[#5f6368] dark:text-[#9aa0a6] whitespace-pre-wrap">{results.soap_note.objective}</p>
                          </div>
                        )}
                        {results.soap_note.assessment && (
                          <div className="bg-orange-50 dark:bg-orange-900/10 rounded-lg p-4 border-l-4 border-orange-500">
                            <p className="font-medium text-orange-700 dark:text-orange-400 mb-1">Assessment:</p>
                            <p className="text-[#5f6368] dark:text-[#9aa0a6] whitespace-pre-wrap">{results.soap_note.assessment}</p>
                          </div>
                        )}
                        {results.soap_note.plan && (
                          <div className="bg-purple-50 dark:bg-purple-900/10 rounded-lg p-4 border-l-4 border-purple-500">
                            <p className="font-medium text-purple-700 dark:text-purple-400 mb-1">Plan:</p>
                            <p className="text-[#5f6368] dark:text-[#9aa0a6] whitespace-pre-wrap">{results.soap_note.plan}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Metadata */}
                  {results.metadata && (
                    <div className="pt-4 border-t border-[#e2e8f0] dark:border-[#5f6368] text-xs text-[#9aa0a6] dark:text-[#5f6368]">
                      <p>Processing Time: {results.metadata.processing_time?.toFixed(2)}s</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => {
                  setResults(null)
                  setError(null)
                  setStatus(null)
                }}
                className="w-full bg-[#4285f4] dark:bg-[#1a73e8] text-white py-3 px-6 rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] transition-colors font-medium shadow-md hover:shadow-lg"
              >
                New Analysis
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}