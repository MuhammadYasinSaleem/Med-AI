import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import LabAnalyzer from './pages/LabAnalyzer'
import Interview from './pages/Interview'
import Triage from './pages/Triage'
import MedicationInteraction from './pages/MedicationInteraction'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lab-analyzer" element={<LabAnalyzer />} />
          <Route path="/interview" element={<Interview />} />
          <Route path="/triage" element={<Triage />} />
          <Route path="/medication-interaction" element={<MedicationInteraction />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
