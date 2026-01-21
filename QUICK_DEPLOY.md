# Quick Deployment Checklist

## ✅ Issues Fixed

1. **Frontend API URL** - Now uses `VITE_API_BASE_URL` environment variable
2. **Backend CORS** - Now supports `CORS_ALLOWED_ORIGINS` environment variable

## 🚀 Quick Start

### Backend

1. Create `backend/.env`:
```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
GEMINI_API_KEY=your-api-key
```

2. Deploy:
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
gunicorn medai.wsgi:application --bind 0.0.0.0:8000
```

### Frontend

1. Create `frontend/.env`:
```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

2. Build & Deploy:
```bash
cd frontend
npm install
npm run build
# Deploy dist/ folder to your hosting
```

## 📝 Key Changes Made

- `frontend/src/services/api.js` - Now uses `import.meta.env.VITE_API_BASE_URL`
- `backend/medai/settings.py` - CORS now reads from `CORS_ALLOWED_ORIGINS` env var

See `DEPLOYMENT.md` for detailed instructions.
