# Deployment Guide

This guide will help you deploy the MedAI system to production.

## Issues Fixed for Deployment

1. ✅ **API URL Configuration** - Frontend now uses environment variables
2. ✅ **CORS Configuration** - Backend CORS supports environment variables
3. ✅ **Environment Variables** - Both frontend and backend support .env files

## Prerequisites

- Python 3.8+ (for backend)
- Node.js 18+ (for frontend)
- PostgreSQL (optional, SQLite works for development)
- Redis (for Celery, optional)
- Google Gemini API Key

## Backend Deployment

### 1. Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Database (PostgreSQL recommended for production)
DB_NAME=medai_db
DB_USER=medai_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# CORS - Add your frontend domain(s)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Optional: Redis for Celery
REDIS_URL=redis://localhost:6379/0
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Database Setup

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run with Gunicorn (Production)

```bash
gunicorn medai.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 6. Using Nginx (Recommended)

Create an Nginx configuration file:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/backend/staticfiles/;
    }

    location /media/ {
        alias /path/to/backend/media/;
    }
}
```

## Frontend Deployment

### 1. Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

Or for development:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 2. Install Dependencies

```bash
cd frontend
npm install
```

### 3. Build for Production

```bash
npm run build
```

This creates a `dist/` folder with optimized production files.

### 4. Deploy Options

#### Option A: Deploy to Vercel/Netlify

1. Connect your repository
2. Set environment variable: `VITE_API_BASE_URL=https://api.yourdomain.com`
3. Build command: `npm run build`
4. Output directory: `dist`

#### Option B: Deploy with Nginx

1. Copy `dist/` folder to your server
2. Configure Nginx:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

#### Option C: Serve with Node.js

```bash
npm install -g serve
serve -s dist -l 3000
```

## Docker Deployment (Optional)

### Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "medai.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./backend/media:/app/media
      - ./backend/staticfiles:/app/staticfiles

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_BASE_URL=http://backend:8000
    depends_on:
      - backend
```

## Common Deployment Issues

### 1. CORS Errors

**Problem**: Frontend can't connect to backend API

**Solution**: 
- Ensure `CORS_ALLOWED_ORIGINS` in backend `.env` includes your frontend URL
- Check that URLs match exactly (including http/https and ports)

### 2. API Connection Failed

**Problem**: Frontend shows "Network Error" or "Connection Refused"

**Solution**:
- Verify `VITE_API_BASE_URL` is set correctly in frontend `.env`
- Ensure backend is running and accessible
- Check firewall rules

### 3. Static Files Not Loading

**Problem**: CSS/JS files return 404

**Solution**:
- Run `python manage.py collectstatic`
- Configure web server to serve static files
- Check `STATIC_URL` and `STATIC_ROOT` in settings.py

### 4. Environment Variables Not Working

**Problem**: Changes to `.env` don't take effect

**Solution**:
- Restart the server after changing `.env`
- For frontend: Rebuild with `npm run build` after changing `.env`
- Verify `.env` file is in the correct directory

## Security Checklist

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use HTTPS in production
- [ ] Keep API keys secure (use environment variables)
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging

## Testing Deployment

1. **Backend Health Check**:
   ```bash
   curl https://api.yourdomain.com/health/
   ```

2. **Frontend**:
   - Visit your frontend URL
   - Check browser console for errors
   - Test all features (Lab Analyzer, Interview, Triage, Medication Interaction)

3. **API Endpoints**:
   ```bash
   curl https://api.yourdomain.com/api/upload/
   ```

## Support

For issues or questions, check:
- Backend logs: `backend/logs/django.log`
- Browser console for frontend errors
- Server logs (Nginx, Gunicorn, etc.)
