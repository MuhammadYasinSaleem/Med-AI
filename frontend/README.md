# MedAI Frontend

## Overview

The MedAI Frontend is a unified React application that integrates all three medical AI services:

1. **Lab Report Analyzer** (Hassan) - AI-powered lab report analysis with critical value detection
2. **Clinical Interview & Triage** (Abdullah) - Multi-step patient interviews with automated triage
3. **Medication Interaction Checker** (Faizan) - Drug-drug and drug-disease interaction analysis

## Features

### 🏠 Home Page
- Clean, Google-inspired design
- Quick access to all three services
- Search functionality
- Feature cards with descriptions

### 📄 Lab Report Analyzer
- Upload lab reports (PDF, JPG, JPEG, PNG)
- Patient information form
- Multi-language support (English, Urdu, Punjabi, Pashto, Sindhi)
- Real-time processing status
- Detailed analysis results:
  - Humanistic summary
  - Critical findings with urgency indicators
  - Abnormal findings
  - Normal findings
  - SOAP notes
- PDF download (always in English for clinical documentation)

### 💬 Clinical Interview & Triage
- Start patient interviews in multiple languages
- Interactive conversation flow
- Quick triage assessment
- Automated symptom extraction
- Clinical summary generation
- PDF report download

### 💊 Medication Interaction Checker
- Patient information (age, conditions)
- Multiple medication input
- Mark medications as "new" or existing
- Severity classification:
  - CONTRAINDICATED
  - MAJOR
  - MODERATE
  - MINOR
- Detailed findings and SOAP notes
- Interaction graph visualization

## Technology Stack

- **React 18** - UI framework
- **React Router** - Navigation
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Vite** - Build tool

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── Layout.jsx          # Main layout with navigation
│   ├── pages/
│   │   ├── Home.jsx            # Landing page
│   │   ├── LabAnalyzer.jsx     # Lab report analyzer
│   │   ├── Interview.jsx       # Clinical interview & triage
│   │   └── MedicationInteraction.jsx  # Medication checker
│   ├── services/
│   │   └── api.js              # API client configuration
│   ├── App.jsx                 # Main app component
│   └── main.jsx                # Entry point
├── package.json
└── vite.config.js
```

## Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Build for production**
   ```bash
   npm run build
   ```

## API Configuration

The frontend connects to the Django backend at `http://localhost:8000` by default.

To change the API base URL, edit `src/services/api.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000'  // Change this
```

## Backend Endpoints

### Lab Analyzer
- `POST /api/upload/` - Upload lab report
- `GET /status/<report_id>/api/` - Get processing status
- `GET /api/results/<report_id>/` - Get analysis results
- `GET /results/<report_id>/download/` - Download PDF summary

### Clinical Interview
- `POST /medai/interview/start/` - Start interview session
- `POST /medai/interview/answer/` - Submit answer
- `POST /medai/interview/summary/` - Generate clinical summary
- `POST /medai/interview/triage/` - Quick triage assessment

### Medication Interaction
- `POST /medai/medication_interaction/analyze_interaction/` - Analyze interactions

## Usage

### Lab Report Analyzer

1. Navigate to `/lab-analyzer`
2. Fill in patient information:
   - Name, age, gender
   - Preferred language
   - Pregnancy status (if applicable)
3. Upload lab report file (PDF, JPG, JPEG, PNG)
4. Click "Analyze Report"
5. View results and download PDF summary

### Clinical Interview

1. Navigate to `/interview`
2. Select language preference
3. Click "Start Interview" or use "Quick Triage Assessment"
4. Answer questions as they appear
5. Generate clinical summary when complete
6. Download PDF report

### Medication Interaction

1. Navigate to `/medication-interaction`
2. Enter patient age and conditions
3. Add medications (mark "New" if considering prescription)
4. Click "Check Interactions"
5. Review severity and findings

## Design System

The frontend uses a Google-inspired design system:

- **Primary Color**: `#4285f4` (Google Blue)
- **Text Colors**: 
  - Primary: `#202124`
  - Secondary: `#5f6368`
  - Muted: `#9aa0a6`
- **Background**: `#ffffff` (white)
- **Borders**: `#dfe1e5`, `#e8eaed`
- **Hover States**: `#f1f3f4`, `#f8f9fa`

## Features by Service

### Lab Analyzer Features
- ✅ File upload with drag & drop
- ✅ Real-time status polling
- ✅ Multi-language support
- ✅ Critical findings highlighting
- ✅ PDF download (English only)
- ✅ Error handling with quota detection

### Interview Features
- ✅ Multi-language interviews
- ✅ Conversation history
- ✅ Quick triage assessment
- ✅ Clinical summary generation
- ✅ PDF report download

### Medication Interaction Features
- ✅ Patient context awareness
- ✅ Multiple medication support
- ✅ New vs. existing medication tracking
- ✅ Severity classification
- ✅ SOAP note generation
- ✅ Interaction graph visualization

## Development

### Running Locally

1. **Start backend server** (in separate terminal)
   ```bash
   cd ../backend/ai-hackathon-techverse2-team-delta/medai
   python manage.py runserver
   ```

2. **Start frontend dev server**
   ```bash
   npm run dev
   ```

3. **Access application**
   - Frontend: `http://localhost:5173`
   - Backend: `http://localhost:8000`

### Environment Variables

Create a `.env` file in the frontend directory if needed:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Then update `api.js` to use:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
```

## Troubleshooting

### CORS Errors
- Ensure backend CORS is configured to allow `http://localhost:5173`
- Check `backend/medai/settings.py` for `CORS_ALLOWED_ORIGINS`

### API Connection Issues
- Verify backend server is running on port 8000
- Check browser console for detailed error messages
- Verify API endpoints match backend URLs

### File Upload Issues
- Check file size (max 10MB)
- Verify file format (PDF, JPG, JPEG, PNG)
- Check browser console for validation errors

## Production Deployment

1. **Build the application**
   ```bash
   npm run build
   ```

2. **Serve static files**
   - Use a web server (nginx, Apache)
   - Or deploy to Vercel, Netlify, etc.

3. **Update API base URL**
   - Set production backend URL
   - Update CORS settings on backend

## Contributing

This is a unified frontend for the MedAI hackathon project. All three team members' services are integrated:

- **Hassan**: Lab Report Analyzer
- **Abdullah**: Clinical Interview & Triage
- **Faizan**: Medication Interaction Checker

## License

Part of the TechVerse2 Team Delta hackathon project.

---

**Built with React, Tailwind CSS, and ❤️**
