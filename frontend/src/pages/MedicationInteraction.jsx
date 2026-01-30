import { useState, useMemo, useEffect } from 'react'
import { Pill, Search, Loader2, AlertTriangle, CheckCircle, XCircle, Network } from 'lucide-react'
import { medicationAPI } from '../services/api'
import { useTheme } from '../contexts/ThemeContext'

// Interaction Graph Component
const InteractionGraph = ({ interactionGraph }) => {
  const { theme } = useTheme()
  const textColor = theme === 'dark' ? '#9aa0a6' : '#5f6368'
  
  const graphData = useMemo(() => {
    if (!interactionGraph) return null

    const nodes = []
    const edges = []
    const nodeMap = new Map()
    let nodeId = 0

    // Add drug-drug interactions
    if (interactionGraph.drug_drug && Array.isArray(interactionGraph.drug_drug)) {
      interactionGraph.drug_drug.forEach((interaction) => {
        const relation = interaction.relation || ''
        const [drug1, drug2] = relation.split('+').map(d => d.trim()).filter(Boolean)
        
        if (drug1 && drug2) {
          if (!nodeMap.has(drug1)) {
            nodeMap.set(drug1, nodeId++)
            nodes.push({
              id: nodeMap.get(drug1),
              label: drug1,
              type: 'drug',
              risk: interaction.risk || 'unknown'
            })
          }
          if (!nodeMap.has(drug2)) {
            nodeMap.set(drug2, nodeId++)
            nodes.push({
              id: nodeMap.get(drug2),
              label: drug2,
              type: 'drug',
              risk: interaction.risk || 'unknown'
            })
          }
          edges.push({
            source: nodeMap.get(drug1),
            target: nodeMap.get(drug2),
            type: 'drug_drug',
            effect: interaction.effect || '',
            risk: interaction.risk || 'unknown'
          })
        }
      })
    }

    // Add drug-disease interactions
    if (interactionGraph.drug_disease && Array.isArray(interactionGraph.drug_disease)) {
      interactionGraph.drug_disease.forEach((interaction) => {
        const relation = interaction.relation || ''
        const parts = relation.split('+').map(d => d.trim()).filter(Boolean)
        if (parts.length >= 2) {
          const drug = parts[0]
          const condition = parts.slice(1).join(' + ')
          
          if (!nodeMap.has(drug)) {
            nodeMap.set(drug, nodeId++)
            nodes.push({
              id: nodeMap.get(drug),
              label: drug,
              type: 'drug',
              risk: interaction.risk || 'unknown'
            })
          }
          if (!nodeMap.has(condition)) {
            nodeMap.set(condition, nodeId++)
            nodes.push({
              id: nodeMap.get(condition),
              label: condition,
              type: 'condition',
              risk: interaction.risk || 'unknown'
            })
          }
          edges.push({
            source: nodeMap.get(drug),
            target: nodeMap.get(condition),
            type: 'drug_disease',
            effect: interaction.effect || '',
            risk: interaction.risk || 'unknown'
          })
        }
      })
    }

    // Add drug-food interactions
    if (interactionGraph.drug_food && Array.isArray(interactionGraph.drug_food)) {
      interactionGraph.drug_food.forEach((interaction) => {
        const relation = interaction.relation || ''
        const parts = relation.split('+').map(d => d.trim()).filter(Boolean)
        if (parts.length >= 2) {
          const drug = parts[0]
          const food = parts.slice(1).join(' + ')
          
          if (!nodeMap.has(drug)) {
            nodeMap.set(drug, nodeId++)
            nodes.push({
              id: nodeMap.get(drug),
              label: drug,
              type: 'drug',
              risk: 'minor'
            })
          }
          if (!nodeMap.has(food)) {
            nodeMap.set(food, nodeId++)
            nodes.push({
              id: nodeMap.get(food),
              label: food,
              type: 'food',
              risk: 'minor'
            })
          }
          edges.push({
            source: nodeMap.get(drug),
            target: nodeMap.get(food),
            type: 'drug_food',
            effect: interaction.effect || ''
          })
        }
      })
    }

    return { nodes, edges }
  }, [interactionGraph])

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="text-center py-8 text-[#5f6368] dark:text-[#9aa0a6]">
        <Network className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No interaction graph data available</p>
      </div>
    )
  }

  const getRiskColor = (risk) => {
    const riskLower = (risk || '').toLowerCase()
    if (riskLower.includes('major') || riskLower.includes('contraindicated')) return '#ef4444'
    if (riskLower.includes('moderate')) return '#f59e0b'
    if (riskLower.includes('minor')) return '#10b981'
    return '#6b7280'
  }

  const getNodeColor = (type) => {
    switch (type) {
      case 'drug': return '#3b82f6'
      case 'condition': return '#ef4444'
      case 'food': return '#10b981'
      default: return '#6b7280'
    }
  }

  // Simple force-directed layout simulation
  const layoutNodes = (nodes, edges) => {
    const centerX = 400
    const centerY = 300
    const radius = 200
    
    return nodes.map((node, index) => {
      const angle = (2 * Math.PI * index) / nodes.length
      return {
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      }
    })
  }

  const positionedNodes = layoutNodes(graphData.nodes, graphData.edges)

  return (
    <div className="w-full overflow-auto">
      <div className="bg-[#f8f9fa] dark:bg-[#202124] rounded-lg p-6 min-h-[400px]">
        <svg width="100%" height="400" viewBox="0 0 800 600" className="w-full">
          {/* Draw edges first (so they appear behind nodes) */}
          {graphData.edges.map((edge, idx) => {
            const sourceNode = positionedNodes.find(n => n.id === edge.source)
            const targetNode = positionedNodes.find(n => n.id === edge.target)
            if (!sourceNode || !targetNode) return null
            
            const color = getRiskColor(edge.risk)
            return (
              <line
                key={`edge-${idx}`}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke={color}
                strokeWidth={2}
                opacity={0.4}
                strokeDasharray={edge.type === 'drug_food' ? '5,5' : '0'}
              />
            )
          })}

          {/* Draw nodes */}
          {positionedNodes.map((node) => {
            const color = getNodeColor(node.type)
            const riskColor = getRiskColor(node.risk)
            return (
              <g key={`node-${node.id}`}>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.type === 'drug' ? 25 : 20}
                  fill={color}
                  stroke={riskColor}
                  strokeWidth={3}
                  className="cursor-pointer hover:opacity-80 transition-opacity"
                />
                <text
                  x={node.x}
                  y={node.y + 5}
                  textAnchor="middle"
                  fill="white"
                  fontSize="10"
                  fontWeight="bold"
                  className="pointer-events-none"
                >
                  {node.type === 'drug' ? 'D' : node.type === 'condition' ? 'C' : 'F'}
                </text>
                <text
                  x={node.x}
                  y={node.y + 40}
                  textAnchor="middle"
                  fill={textColor}
                  fontSize="11"
                  fontWeight="500"
                  className="pointer-events-none"
                >
                  {node.label.length > 15 ? node.label.substring(0, 15) + '...' : node.label}
                </text>
              </g>
            )
          })}
        </svg>

        {/* Legend */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-500"></div>
            <span className="text-[#5f6368] dark:text-[#9aa0a6]">Drug</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-[#5f6368] dark:text-[#9aa0a6]">Condition</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-[#5f6368] dark:text-[#9aa0a6]">Food</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-red-500 rounded-full"></div>
            <span className="text-[#5f6368] dark:text-[#9aa0a6]">High Risk</span>
          </div>
        </div>

        {/* Interaction Details */}
        <div className="mt-6 space-y-3">
          {graphData.edges.map((edge, idx) => {
            const sourceNode = positionedNodes.find(n => n.id === edge.source)
            const targetNode = positionedNodes.find(n => n.id === edge.target)
            if (!sourceNode || !targetNode) return null
            
            const riskColor = getRiskColor(edge.risk)
            return (
              <div
                key={`detail-${idx}`}
                className="bg-white dark:bg-[#303134] rounded-lg p-3 border-l-4"
                style={{ borderLeftColor: riskColor }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-[#202124] dark:text-[#e8eaed] text-sm">
                      {sourceNode.label} ↔ {targetNode.label}
                    </p>
                    <p className="text-xs text-[#5f6368] dark:text-[#9aa0a6] mt-1">
                      {edge.effect}
                    </p>
                  </div>
                  {edge.risk && (
                    <span
                      className="px-2 py-1 rounded text-xs font-medium ml-2"
                      style={{
                        backgroundColor: riskColor + '20',
                        color: riskColor
                      }}
                    >
                      {edge.risk.toUpperCase()}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default function MedicationInteraction() {
  const [formData, setFormData] = useState({
    patient_age: '',
    conditions: '',
    language: 'english',
    medications: [{ name: '', is_new: false }],
  })
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Debug: Log when results change
  useEffect(() => {
    console.log('Results state changed:', results)
    if (results) {
      console.log('Results severity:', results.severity)
      console.log('Results keys:', Object.keys(results))
    }
  }, [results])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const addMedication = () => {
    setFormData(prev => ({
      ...prev,
      medications: [...prev.medications, { name: '', is_new: false }]
    }))
  }

  const removeMedication = (index) => {
    if (formData.medications.length > 1) {
      setFormData(prev => ({
        ...prev,
        medications: prev.medications.filter((_, i) => i !== index)
      }))
    }
  }

  const updateMedication = (index, field, value) => {
    setFormData(prev => {
      const updated = [...prev.medications]
      updated[index] = { ...updated[index], [field]: value }
      return { ...prev, medications: updated }
    })
  }

  const parseSOAPNote = (soapNote) => {
    if (!soapNote) return null

    const sections = {
      S: '',
      O: '',
      A: '',
      P: ''
    }

    // Try full word format first: "Subjective: ... Objective: ... Assessment: ... Plan: ..."
    const subjectiveMatch = soapNote.match(/Subjective[:\s]+(.*?)(?=Objective|Assessment|Plan|$)/is)
    const objectiveMatch = soapNote.match(/Objective[:\s]+(.*?)(?=Assessment|Plan|$)/is)
    const assessmentMatch = soapNote.match(/Assessment[:\s]+(.*?)(?=Plan|$)/is)
    const planMatch = soapNote.match(/Plan[:\s]+(.*?)$/is)

    if (subjectiveMatch || objectiveMatch || assessmentMatch || planMatch) {
      sections.S = subjectiveMatch ? subjectiveMatch[1].trim() : ''
      sections.O = objectiveMatch ? objectiveMatch[1].trim() : ''
      sections.A = assessmentMatch ? assessmentMatch[1].trim() : ''
      sections.P = planMatch ? planMatch[1].trim() : ''
      // Only return if at least one section was found
      if (sections.S || sections.O || sections.A || sections.P) {
        return sections
      }
    }

    // Try single letter format with line breaks: "S: ...\nO: ...\nA: ...\nP: ..."
    const sMatch = soapNote.match(/^S[:\s]+(.*?)(?=^O[:\s]|^A[:\s]|^P[:\s]|$)/ims)
    const oMatch = soapNote.match(/^O[:\s]+(.*?)(?=^A[:\s]|^P[:\s]|$)/ims)
    const aMatch = soapNote.match(/^A[:\s]+(.*?)(?=^P[:\s]|$)/ims)
    const pMatch = soapNote.match(/^P[:\s]+(.*?)$/ims)

    if (sMatch || oMatch || aMatch || pMatch) {
      sections.S = sMatch ? sMatch[1].trim() : ''
      sections.O = oMatch ? oMatch[1].trim() : ''
      sections.A = aMatch ? aMatch[1].trim() : ''
      sections.P = pMatch ? pMatch[1].trim() : ''
      if (sections.S || sections.O || sections.A || sections.P) {
        return sections
      }
    }

    // Try inline format: "S: ... O: ... A: ... P: ..."
    const inlineSMatch = soapNote.match(/\bS[:\s]+(.*?)(?=\bO[:\s]|\bA[:\s]|\bP[:\s]|$)/is)
    const inlineOMatch = soapNote.match(/\bO[:\s]+(.*?)(?=\bA[:\s]|\bP[:\s]|$)/is)
    const inlineAMatch = soapNote.match(/\bA[:\s]+(.*?)(?=\bP[:\s]|$)/is)
    const inlinePMatch = soapNote.match(/\bP[:\s]+(.*?)$/is)

    if (inlineSMatch || inlineOMatch || inlineAMatch || inlinePMatch) {
      sections.S = inlineSMatch ? inlineSMatch[1].trim() : ''
      sections.O = inlineOMatch ? inlineOMatch[1].trim() : ''
      sections.A = inlineAMatch ? inlineAMatch[1].trim() : ''
      sections.P = inlinePMatch ? inlinePMatch[1].trim() : ''
      if (sections.S || sections.O || sections.A || sections.P) {
        return sections
      }
    }

    // If no clear sections found, try splitting by double newlines or common separators
    const paragraphs = soapNote.split(/\n\s*\n/).filter(p => p.trim())
    if (paragraphs.length >= 4) {
      sections.S = paragraphs[0].replace(/^(S|Subjective)[:\s]+/i, '').trim()
      sections.O = paragraphs[1].replace(/^(O|Objective)[:\s]+/i, '').trim()
      sections.A = paragraphs[2].replace(/^(A|Assessment)[:\s]+/i, '').trim()
      sections.P = paragraphs[3].replace(/^(P|Plan)[:\s]+/i, '').trim()
      if (sections.S || sections.O || sections.A || sections.P) {
        return sections
      }
    }

    // If all else fails, return null to show as plain text
    return null
  }

  const analyzeInteraction = async () => {
    const validMedications = formData.medications.filter(m => m.name.trim())
    
    if (validMedications.length < 1) {
      setError('Please enter at least 1 medication to check for interactions')
      return
    }

    if (!formData.patient_age || formData.patient_age < 0) {
      setError('Please enter a valid patient age')
      return
    }

    if (!formData.conditions.trim()) {
      setError('Please enter patient conditions (e.g., "None", "Diabetes", "CKD Stage 3")')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await medicationAPI.analyzeInteraction({
        language: formData.language,
        patient_age: parseInt(formData.patient_age),
        conditions: formData.conditions,
        medications: validMedications,
      })
      
      // Log the response for debugging
      console.log('API Response:', response)
      console.log('Response Data:', response.data)
      console.log('Response Status:', response.status)
      
      // Ensure we have the expected data structure
      // Axios wraps the response, so check both response.data and direct response
      const responseData = response?.data || response
      
      console.log('Full response object:', response)
      console.log('Response data:', responseData)
      console.log('Response data type:', typeof responseData)
      console.log('Is responseData an object?', responseData && typeof responseData === 'object')
      
      if (responseData && typeof responseData === 'object') {
        console.log('Setting results with:', responseData)
        console.log('Results severity:', responseData.severity)
        console.log('Results findings:', responseData.findings)
        console.log('Results interaction_graph:', responseData.interaction_graph)
        
        // Validate that we have at least severity
        if (responseData.severity) {
          // Force a state update by creating a new object
          setResults({ ...responseData })
          console.log('Results state updated successfully')
          
          // Double check after a brief delay
          setTimeout(() => {
            console.log('State check after update - results should be set now')
          }, 100)
        } else {
          console.error('Response missing severity field:', responseData)
          console.error('Available keys:', Object.keys(responseData))
          setError('Invalid response: missing severity field. Available keys: ' + Object.keys(responseData).join(', '))
        }
      } else {
        setError('Invalid response format from server')
        console.error('Invalid response:', response)
        console.error('Response data:', responseData)
      }
    } catch (err) {
      console.error('Error analyzing interaction:', err)
      console.error('Error details:', {
        message: err.message,
        response: err.response,
        data: err.response?.data
      })
      setError(
        err.response?.data?.error || 
        err.response?.data?.detail ||
        err.message || 
        'Failed to analyze medication interactions'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-4 py-8 min-h-screen bg-white dark:bg-[#1a1a1a]">
      <div className="max-w-4xl mx-auto">
        {/* Input Section - Gemini Style */}
        {!results && (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-semibold text-[#202124] dark:text-[#e8eaed] mb-2">Medication Interaction Checker</h2>
              <p className="text-[#5f6368] dark:text-[#9aa0a6]">
                Analyze potential interactions between medications and patient conditions
              </p>
            </div>
            
            <div className="w-full max-w-2xl space-y-6">
              <div className="bg-white dark:bg-[#303134] rounded-2xl shadow-lg p-8 border border-[#e2e8f0] dark:border-[#5f6368] transition-colors">
          
                {/* Patient Info */}
                <div className="space-y-4 mb-6">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-2">
                        Patient Age *
                      </label>
                      <input
                        type="number"
                        name="patient_age"
                        value={formData.patient_age}
                        onChange={handleInputChange}
                        min="0"
                        max="150"
                        className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md"
                        placeholder="Age in years"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-2">
                        Language
                      </label>
                      <select
                        name="language"
                        value={formData.language}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md"
                      >
                        <option value="english">English</option>
                        <option value="urdu">Urdu</option>
                        <option value="roman_urdu">Roman Urdu</option>
                      </select>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-2">
                      Conditions *
                    </label>
                    <input
                      type="text"
                      name="conditions"
                      value={formData.conditions}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md placeholder-[#9aa0a6] dark:placeholder-[#5f6368]"
                      placeholder="e.g., CKD Stage 3, Diabetes"
                      required
                    />
                  </div>
                </div>
          
                {/* Medications */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-3">
                    Medications *
                  </label>
                  <div className="space-y-3">
                    {formData.medications.map((med, index) => (
                      <div key={index} className="flex gap-2 items-center">
                        <input
                          type="text"
                          value={med.name}
                          onChange={(e) => updateMedication(index, 'name', e.target.value)}
                          placeholder={`Medication ${index + 1} (e.g., Metformin, Ibuprofen)`}
                          className="flex-1 px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] text-[#202124] dark:text-[#e8eaed] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] transition-all shadow-sm hover:shadow-md placeholder-[#9aa0a6] dark:placeholder-[#5f6368]"
                        />
                        <label className="flex items-center gap-2 px-4 py-3 border border-[#dfe1e5] dark:border-[#5f6368] bg-white dark:bg-[#202124] rounded-xl cursor-pointer hover:bg-[#f8f9fa] dark:hover:bg-[#303134] transition-colors shadow-sm">
                          <input
                            type="checkbox"
                            checked={med.is_new}
                            onChange={(e) => updateMedication(index, 'is_new', e.target.checked)}
                            className="w-4 h-4 text-[#4285f4] dark:text-[#8ab4f8] border-[#dfe1e5] dark:border-[#5f6368] rounded focus:ring-[#4285f4] dark:focus:ring-[#8ab4f8] bg-white dark:bg-[#202124]"
                          />
                          <span className="text-sm text-[#5f6368] dark:text-[#9aa0a6]">New</span>
                        </label>
                        {formData.medications.length > 1 && (
                          <button
                            onClick={() => removeMedication(index)}
                            className="px-3 py-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-xl hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                          >
                            <XCircle className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={addMedication}
                    className="px-4 py-3 bg-white dark:bg-[#202124] border border-[#dfe1e5] dark:border-[#5f6368] text-[#202124] dark:text-[#e8eaed] rounded-full hover:bg-[#f8f9fa] dark:hover:bg-[#303134] transition-colors font-medium shadow-sm hover:shadow-md"
                  >
                    + Add Medication
                  </button>
                  <button
                    onClick={analyzeInteraction}
                    disabled={loading || formData.medications.filter(m => m.name.trim()).length < 1}
                    className="flex-1 bg-[#4285f4] dark:bg-[#1a73e8] text-white py-3 px-6 rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] disabled:bg-[#9aa0a6] disabled:cursor-not-allowed flex items-center justify-center transition-colors font-medium shadow-md hover:shadow-lg text-base"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Search className="w-5 h-5 mr-2" />
                        Check Interactions
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mt-6 max-w-2xl w-full bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-4">
                  <div className="flex items-start">
                    <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-medium text-red-800 dark:text-red-400">Error</h3>
                      <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Info Section */}
              <div className="mt-12 max-w-2xl w-full">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl p-6">
                  <div className="flex items-start">
                    <Pill className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">Important Note</h3>
                      <p className="text-sm text-blue-800 dark:text-blue-300">
                        This tool is for informational purposes only. Always consult with a healthcare
                        professional before making any changes to your medication regimen. Mark medications as "New" if they are being considered for prescription.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Display (when results exist) */}
        {error && results && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-4">
            <div className="flex items-start">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mr-2 flex-shrink-0 mt-0.5" />
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
                  {results.severity === 'CONTRAINDICATED' || results.severity === 'MAJOR' ? (
                    <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
                  ) : results.severity === 'MODERATE' ? (
                    <AlertTriangle className="w-8 h-8 text-orange-600 dark:text-orange-400" />
                  ) : (
                    <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                  )}
                </div>
                <h2 className="text-3xl font-semibold text-[#202124] dark:text-[#e8eaed] mb-2">Analysis Complete</h2>
                <p className="text-[#5f6368] dark:text-[#9aa0a6]">Medication interaction results</p>
              </div>

              {/* Result Card */}
              <div className="bg-white dark:bg-[#303134] rounded-2xl shadow-lg p-8 border border-[#e2e8f0] dark:border-[#5f6368]">
                <div className="space-y-6">
                  {/* Severity */}
                  <div className="flex items-center justify-between p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                    <div>
                      <span className="block text-sm font-medium text-[#5f6368] dark:text-[#9aa0a6] mb-1">
                        Severity Level
                      </span>
                      <span className={`inline-block font-bold text-2xl px-5 py-2 rounded-full mt-2 ${
                        results.severity === 'CONTRAINDICATED' || results.severity === 'MAJOR'
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                          : results.severity === 'MODERATE'
                          ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                          : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                      }`}>
                        {results.severity}
                      </span>
                    </div>
                    <div className={`w-4 h-4 rounded-full ${
                      results.severity === 'CONTRAINDICATED' || results.severity === 'MAJOR'
                        ? 'bg-red-500'
                        : results.severity === 'MODERATE'
                        ? 'bg-orange-500'
                        : 'bg-green-500'
                    }`} />
                  </div>

                  {/* Findings */}
                  {results.findings && results.findings.length > 0 && (
                    <div className="p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                      <h3 className="font-semibold text-[#202124] dark:text-[#e8eaed] mb-4">Findings:</h3>
                      <ul className="space-y-3">
                        {results.findings.map((finding, idx) => (
                          <li key={idx} className="flex items-start gap-3">
                            <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                              results.severity === 'CONTRAINDICATED' || results.severity === 'MAJOR'
                                ? 'bg-red-500'
                                : results.severity === 'MODERATE'
                                ? 'bg-orange-500'
                                : 'bg-green-500'
                            }`} />
                            <span className="text-[#202124] dark:text-[#e8eaed] leading-relaxed">
                              {typeof finding === 'string' ? finding : JSON.stringify(finding)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* SOAP Note */}
                  {results.soap_note && (() => {
                    const soapSections = parseSOAPNote(results.soap_note)
                    return (
                      <div className="p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                        <h3 className="font-semibold text-[#202124] dark:text-[#e8eaed] mb-4">Clinical Summary (SOAP):</h3>
                    {soapSections ? (
                      <div className="space-y-4">
                        {soapSections.S && (
                          <div className="bg-blue-50 dark:bg-blue-900/10 rounded-lg p-4 border-l-4 border-blue-500">
                            <h4 className="font-semibold text-blue-700 dark:text-blue-400 mb-2 flex items-center gap-2">
                              <span className="text-lg font-bold">S</span>
                              <span className="text-sm">Subjective</span>
                            </h4>
                            <p className="text-[#5f6368] dark:text-[#9aa0a6] whitespace-pre-wrap">{soapSections.S}</p>
                          </div>
                        )}
                        {soapSections.O && (
                          <div className="bg-green-50 dark:bg-green-900/10 rounded-lg p-4 border-l-4 border-green-500">
                            <h4 className="font-semibold text-green-700 dark:text-green-400 mb-2 flex items-center gap-2">
                              <span className="text-lg font-bold">O</span>
                              <span className="text-sm">Objective</span>
                            </h4>
                            <p className="text-[#5f6368] dark:text-[#9aa0a6] whitespace-pre-wrap">{soapSections.O}</p>
                          </div>
                        )}
                        {soapSections.A && (
                          <div className="bg-orange-50 dark:bg-orange-900/10 rounded-lg p-4 border-l-4 border-orange-500">
                            <h4 className="font-semibold text-orange-700 dark:text-orange-400 mb-2 flex items-center gap-2">
                              <span className="text-lg font-bold">A</span>
                              <span className="text-sm">Assessment</span>
                            </h4>
                            <p className="text-[#5f6368] dark:text-[#9aa0a6] whitespace-pre-wrap">{soapSections.A}</p>
                          </div>
                        )}
                        {soapSections.P && (
                          <div className="bg-purple-50 dark:bg-purple-900/10 rounded-lg p-4 border-l-4 border-purple-500">
                            <h4 className="font-semibold text-purple-700 dark:text-purple-400 mb-2 flex items-center gap-2">
                              <span className="text-lg font-bold">P</span>
                              <span className="text-sm">Plan</span>
                            </h4>
                            <p className="text-[#5f6368] dark:text-[#9aa0a6] whitespace-pre-wrap">{soapSections.P}</p>
                          </div>
                        )}
                      </div>
                      ) : (
                        <p className="text-[#202124] dark:text-[#e8eaed] whitespace-pre-wrap leading-relaxed">{results.soap_note}</p>
                      )}
                      </div>
                    )
                  })()}

                  {/* Interaction Graph */}
                  {results.interaction_graph && Object.keys(results.interaction_graph).length > 0 && (
                    <div className="p-6 rounded-xl bg-[#f8f9fa] dark:bg-[#202124] border border-[#e2e8f0] dark:border-[#5f6368]">
                      <h3 className="font-semibold text-[#202124] dark:text-[#e8eaed] mb-4 flex items-center gap-2">
                        <Network className="w-5 h-5" />
                        Interaction Graph
                      </h3>
                      <InteractionGraph interactionGraph={results.interaction_graph} />
                    </div>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => {
                  setResults(null)
                  setError(null)
                }}
                className="w-full bg-[#4285f4] dark:bg-[#1a73e8] text-white py-3 px-6 rounded-full hover:bg-[#1967d2] dark:hover:bg-[#1557b0] transition-colors font-medium shadow-md hover:shadow-lg"
              >
                New Analysis
              </button>

              {/* Info Section */}
              <div className="mt-8">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl p-6">
                  <div className="flex items-start">
                    <Pill className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">Important Note</h3>
                      <p className="text-sm text-blue-800 dark:text-blue-300">
                        This tool is for informational purposes only. Always consult with a healthcare
                        professional before making any changes to your medication regimen. Mark medications as "New" if they are being considered for prescription.
                      </p>
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
