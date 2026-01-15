# MedAI - Lab Report Analyzer

AI-powered clinical decision support system for analyzing lab reports with critical value detection and reference range adjustment.

## 🎯 Case Study: Clinical Decision Support - Lab Report Analyzer

**The Problem:** Patients wait weeks to have 15-page lab reports interpreted by a doctor.

**Solution:** This system automatically:
- ✅ Parses lab reports (PDF/Image) into structured data
- ✅ Compares values against reference ranges (age/gender/pregnancy adjusted)
- ✅ Identifies critical values (e.g., K+ > 6.5, Glucose > 400)
- ✅ NEVER diagnoses (flags abnormalities + explains significance only)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Additional Requirements:**
- **Tesseract OCR** (for image processing) - Download from: https://github.com/UB-Mannheim/tesseract/wiki
- **Redis** (optional, for Celery background tasks) - Only needed for async processing

### 2. Set Up Environment Variables

Create a `.env` file in the `medai/` folder:

```env
# Gemini API Key (REQUIRED)
# Get from: https://ai.google.dev/
GOOGLE_API_KEY=AIzaSy-paste-your-key-here
GEMINI_API_KEY=AIzaSy-paste-your-key-here

# Django Secret Key (REQUIRED)
# Generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=paste-generated-key-here

# Development Settings
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Optional - defaults to SQLite if not set)
# For Supabase/PostgreSQL:
# DB_NAME=postgres
# DB_USER=postgres
# DB_PASSWORD=your-password
# DB_HOST=db.your-project.supabase.co
# DB_PORT=5432
```

### 3. Run Migrations

```bash
python manage.py migrate
python manage.py createsuperuser  # Optional: for admin access
```

### 4. Start the Server

```bash
python manage.py runserver
```

Visit: **http://localhost:8000**

---

## 📋 Features

### Core Functionality
- **PDF/Image Upload**: Supports PDF, JPG, PNG formats
- **AI-Powered Analysis**: Uses Google Gemini 2.5 Flash for intelligent report parsing
- **Multilingual Support**: Generate summaries in English, Urdu, Punjabi, Pashto, or Sindhi
- **Critical Value Detection**: Automatically flags dangerous values
- **Reference Range Adjustment**: Adjusts ranges based on:
  - Patient age
  - Gender
  - Pregnancy status
- **SOAP-Style Output**: Structured clinical summaries
- **Safety First**: Never diagnoses, only flags abnormalities

### Database Options

**SQLite (Default):**
- ✅ No setup required
- ✅ Perfect for development/hackathon
- ✅ Included with Django

**Supabase/PostgreSQL (Optional):**
1. Create project at https://supabase.com
2. Get connection details from Settings → Database
3. Add to `.env`:
   ```env
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=your-password
   DB_HOST=db.your-project.supabase.co
   DB_PORT=5432
   ```
4. Install driver: `pip install psycopg2-binary`
5. Run migrations: `python manage.py migrate`

---

## 🧪 Testing

### Quick Test Script

Run the setup script (Windows):
```bash
setup_test.bat
```

### Manual Testing

1. **Start Server:**
   ```bash
   python manage.py runserver
   ```

2. **Upload Lab Report:**
   - Go to http://localhost:8000
   - Fill in patient information (age, gender, pregnancy status)
   - Upload a PDF or image of lab report
   - Click "Upload and Analyze"

3. **View Results:**
   - Status page auto-refreshes during processing
   - Results page shows:
     - Structured lab values
     - Abnormalities flagged
     - Critical values highlighted
     - Clinical summary (SOAP format)

### Test Cases

- ✅ **Normal Upload**: Upload any lab report PDF/image
- ✅ **Critical Values**: Test with K+ > 6.5 or Glucose > 400
- ✅ **Pregnancy Adjustment**: Upload report for pregnant patient
- ✅ **Admin Interface**: Access `/admin` to view all data

---

## 🏗️ Architecture

### Project Structure
```
medai/
├── lab_analyzer/          # Main application
│   ├── models.py         # Patient, LabReport, AnalysisResult
│   ├── views.py          # Upload, status, results views
│   ├── forms.py          # Lab report upload form
│   ├── ai_agents/        # AI processing modules
│   │   ├── parser.py     # PDF/image parsing
│   │   ├── reasoning.py  # GPT-4 analysis
│   │   └── safety.py     # Safety checks
│   └── processing.py      # Synchronous processing
├── templates/             # HTML templates (HTMX)
├── medai/                 # Django project settings
│   ├── settings.py       # Configuration
│   └── urls.py           # URL routing
└── requirements.txt       # Dependencies
```

### Processing Flow

1. **Upload** → User uploads PDF/image with patient info
2. **Parse** → Extract text from PDF/image (PyMuPDF/Tesseract)
3. **Analyze** → GPT-4 analyzes report with patient context
4. **Detect** → Identify abnormalities and critical values
5. **Store** → Save results to database
6. **Display** → Show structured results to user

---

## 🔧 Configuration

### Gemini API

- **Model**: Gemini 2.5 Flash (configurable in settings)
- **API Key**: Set `GOOGLE_API_KEY` or `GEMINI_API_KEY` in `.env`
- **Get API Key**: https://ai.google.dev/

### Processing Mode

**Synchronous (Default):**
- No Celery/Redis needed
- Simple setup
- Processing happens in request

**Asynchronous (Optional):**
- Requires Redis + Celery
- Better for production
- Background task processing

---

## 📊 Database Schema

### Models

**Patient:**
- Name, age, gender, pregnancy status
- Used for reference range adjustment

**LabReport:**
- File upload, patient reference
- Processing status
- Timestamps

**AnalysisResult:**
- Structured lab values
- Abnormalities list
- Critical values
- Clinical summary (SOAP format)

---

## 🛠️ Troubleshooting

**"No module named 'celery'"**
→ Run `pip install -r requirements.txt`

**"Gemini API key not found"**
→ Check `.env` file exists and has `GOOGLE_API_KEY` or `GEMINI_API_KEY`

**"Tesseract not found"**
→ Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki

**"Database connection error"**
→ Check `.env` database credentials (if using PostgreSQL/Supabase)

**"Redis connection error"**
→ Only needed for async processing. Use synchronous mode instead.

---

## 📝 API Endpoints

- `GET /` - Upload form
- `POST /upload/` - Upload lab report
- `GET /status/<id>/` - Check processing status
- `GET /results/<id>/` - View analysis results
- `GET /admin/` - Django admin interface

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate secure `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL (Supabase recommended)
- [ ] Set up proper file storage (S3, etc.)
- [ ] Configure static files serving
- [ ] Set up SSL/HTTPS
- [ ] Use production WSGI server (Gunicorn)

### Docker (Optional)

```bash
docker-compose up
```

---

## 📄 License

This project is developed for AI Healthcare Hackathon - Case Study 6.

---

## 🤝 Contributing

This is a hackathon project. For questions or issues, refer to the case study requirements.

---

## 📞 Support

For setup help:
1. Check `.env` file configuration
2. Verify all dependencies installed
3. Check logs in `logs/django.log`
4. Run `python manage.py check` for configuration issues

---

**Built with:** Django, Google Gemini 2.5 Flash, HTMX, Bootstrap 5

---

## 🏆 Hackathon Compliance (Case Study 6)

✅ **All Requirements Met:**
- ✅ Parses lab reports (PDF/Image) into structured data
- ✅ Compares values against reference ranges (age/gender/pregnancy adjusted)
- ✅ Identifies critical values (K+ > 6.5, Glucose > 400, etc.)
- ✅ NEVER diagnoses (flags abnormalities + explains significance only)
- ✅ Zero false negatives on critical values (SafetyAgent double-checks)
- ✅ Multi-agent architecture (Parser → Reasoning → Safety)
- ✅ Humanistic summary (2-3 lines)
- ✅ Downloadable PDF summary feature
- ✅ Concise, point-by-point results
- ✅ **Multilingual Support**: English, Urdu, Punjabi, Pashto, Sindhi

See `HACKATHON_COMPLIANCE.md` for detailed compliance checklist.
