# API Endpoints - Testing Guide

All available endpoints for testing the Lab Report Analyzer application.

## Base URL
```
http://localhost:8000
```

---

## 📋 Available Endpoints

### 1. **Home / Upload Page**
- **URL:** `/`
- **Method:** `GET`, `POST`
- **Description:** 
  - `GET`: Displays the upload form with patient information fields
  - `POST`: Uploads and processes a lab report
- **Test URL:** `http://localhost:8000/`
- **POST Data:**
  ```json
  {
    "patient_name": "John Doe",
    "age": 35,
    "gender": "M",
    "preferred_language": "en",
    "is_pregnant": false,
    "contact": "optional",
    "file": "<file upload>"
  }
  ```
- **Response:** 
  - Success: Redirects to results page
  - Error: Returns to upload page with error message

---

### 2. **Status Page**
- **URL:** `/status/<report_id>/`
- **Method:** `GET`
- **Description:** Shows processing status of a lab report (auto-refreshes)
- **Test URL:** `http://localhost:8000/status/<uuid>/`
- **Example:** `http://localhost:8000/status/123e4567-e89b-12d3-a456-426614174000/`
- **Response:** HTML page showing processing status

---

### 3. **Status API (JSON)**
- **URL:** `/status/<report_id>/api/`
- **Method:** `GET`
- **Description:** Returns processing status as JSON (for AJAX/HTMX)
- **Test URL:** `http://localhost:8000/status/<uuid>/api/`
- **Example:** `http://localhost:8000/status/123e4567-e89b-12d3-a456-426614174000/api/`
- **Response:**
  ```json
  {
    "status": "processing" | "completed" | "failed",
    "progress": "Parsing document...",
    "report_id": "uuid-string"
  }
  ```

---

### 4. **Results Page**
- **URL:** `/results/<report_id>/`
- **Method:** `GET`
- **Description:** Displays complete analysis results including:
  - Humanistic summary (in selected language)
  - Critical findings
  - Abnormal findings
  - Normal findings
  - SOAP note
  - Download PDF button
- **Test URL:** `http://localhost:8000/results/<uuid>/`
- **Example:** `http://localhost:8000/results/123e4567-e89b-12d3-a456-426614174000/`
- **Response:** HTML page with full analysis results

---

### 5. **Download PDF Summary**
- **URL:** `/results/<report_id>/download/`
- **Method:** `GET`
- **Description:** Downloads analysis summary as PDF
- **Test URL:** `http://localhost:8000/results/<uuid>/download/`
- **Example:** `http://localhost:8000/results/123e4567-e89b-12d3-a456-426614174000/download/`
- **Response:** PDF file download
- **Content:** 
  - Patient information
  - Humanistic summary (multilingual)
  - Critical findings
  - Abnormal findings
  - Normal findings count
  - SOAP note

---

### 6. **Django Admin**
- **URL:** `/admin/`
- **Method:** `GET`, `POST`
- **Description:** Django admin interface for managing:
  - Patients
  - Lab Reports
  - Analysis Results
- **Test URL:** `http://localhost:8000/admin/`
- **Note:** Requires superuser account (create with `python manage.py createsuperuser`)

---

## 🧪 Testing Workflow

### Complete Test Flow:

1. **Upload a Report:**
   ```
   POST http://localhost:8000/
   ```
   - Fill form with patient info
   - Select language (English/Urdu/Punjabi/Pashto/Sindhi)
   - Upload PDF/image file
   - Submit form

2. **Check Status (if async):**
   ```
   GET http://localhost:8000/status/<report_id>/
   ```
   - Or use API: `GET http://localhost:8000/status/<report_id>/api/`

3. **View Results:**
   ```
   GET http://localhost:8000/results/<report_id>/
   ```
   - See analysis in selected language
   - Review findings

4. **Download PDF:**
   ```
   GET http://localhost:8000/results/<report_id>/download/
   ```
   - Download summary PDF

---

## 🔍 Quick Test Commands

### Using cURL:

```bash
# 1. Get upload form
curl http://localhost:8000/

# 2. Check status (replace UUID)
curl http://localhost:8000/status/YOUR-UUID-HERE/api/

# 3. Get results (replace UUID)
curl http://localhost:8000/results/YOUR-UUID-HERE/

# 4. Download PDF (replace UUID)
curl -O http://localhost:8000/results/YOUR-UUID-HERE/download/
```

### Using Browser:

1. **Home:** Navigate to `http://localhost:8000/`
2. **Upload:** Fill form and submit
3. **Results:** Automatically redirected after processing
4. **Download:** Click "Download PDF Summary" button

---

## 📝 Form Fields

When testing the upload endpoint (`POST /`), include:

| Field | Type | Required | Options |
|-------|------|----------|---------|
| `patient_name` | string | Yes | Any text |
| `age` | integer | Yes | 0-150 |
| `gender` | choice | Yes | M, F, O, U |
| `preferred_language` | choice | Yes | en, ur, pa, ps, sd |
| `is_pregnant` | boolean | No | true/false |
| `contact` | string | No | Any text |
| `file` | file | Yes | PDF, JPG, PNG (max 10MB) |

---

## 🌐 Language Support

The `preferred_language` field supports:
- `en` - English
- `ur` - Urdu (اردو)
- `pa` - Punjabi (ਪੰਜਾਬੀ)
- `ps` - Pashto (پښتو)
- `sd` - Sindhi (سنڌي)

All summaries, explanations, and SOAP notes will be generated in the selected language.

---

## ⚠️ Important Notes

1. **Synchronous Processing:** Currently uses synchronous processing (no Celery/Redis needed)
2. **File Size Limit:** Maximum 10MB per file
3. **Supported Formats:** PDF, JPG, JPEG, PNG
4. **UUID Required:** All endpoints except home require a valid UUID
5. **CSRF Protection:** POST requests require CSRF token (included in forms)

---

## 🐛 Error Responses

- **404:** Report ID not found
- **400:** Invalid form data or file
- **500:** Server error (check logs)

---

## 📊 Example Response (Status API)

```json
{
  "status": "completed",
  "progress": "Analysis complete",
  "report_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

**Last Updated:** 2026-01-10
**Version:** 1.0
