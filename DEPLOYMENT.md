# 🚀 Deployment Guide

This guide covers deploying the Calendar Booking Assistant to various hosting platforms.

## 📋 Pre-deployment Checklist

- [ ] Google Cloud Service Account created and configured
- [ ] Google Calendar API enabled
- [ ] Service account has calendar access
- [ ] DeepSeek API key obtained
- [ ] All environment variables documented

## 🌐 Platform-Specific Deployment

### 1. Railway (Recommended)

Railway is great for quick deployments with automatic builds.

#### Backend Deployment:
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and create project
railway login
railway init

# 3. Deploy backend
cd backend
railway up

# 4. Set environment variables in Railway dashboard:
DEEPSEEK_API_KEY=your_key_here
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account"...}
GOOGLE_CALENDAR_ID=primary
```

#### Frontend Deployment:
```bash
# 1. Create new service for frontend
railway init

# 2. Deploy frontend
cd frontend
railway up

# 3. Set environment variables:
BACKEND_URL=https://your-backend-url.railway.app
```

### 2. Render

Render offers free tiers and easy deployment from GitHub.

#### Backend Deployment:
1. Connect your GitHub repository to Render
2. Create new "Web Service"
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables in dashboard

#### Frontend Deployment:
1. Create another "Web Service" for frontend
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
4. Set `BACKEND_URL` environment variable

### 3. Fly.io

Great for global deployment with edge locations.

#### Setup:
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login
```

#### Backend Deployment:
```bash
cd backend
fly launch
# Edit fly.toml as needed
fly deploy
fly secrets set DEEPSEEK_API_KEY=your_key
fly secrets set GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account"...}'
```

#### Frontend Deployment:
```bash
cd frontend
fly launch
fly secrets set BACKEND_URL=https://your-backend.fly.dev
fly deploy
```

### 4. Heroku

Traditional platform with good documentation.

#### Setup:
```bash
# Install Heroku CLI
# Create Procfile for backend:
echo "web: uvicorn main:app --host=0.0.0.0 --port=${PORT:-8000}" > backend/Procfile

# Create Procfile for frontend:
echo "web: streamlit run streamlit_app.py --server.port=${PORT:-8501} --server.address=0.0.0.0" > frontend/Procfile
```

#### Deploy:
```bash
# Backend
cd backend
heroku create your-app-backend
git push heroku main

# Frontend
cd frontend
heroku create your-app-frontend
git push heroku main
```

### 5. Google Cloud Run

Serverless container deployment.

#### Build and Deploy:
```bash
# Backend
cd backend
gcloud builds submit --tag gcr.io/PROJECT_ID/calendar-backend
gcloud run deploy --image gcr.io/PROJECT_ID/calendar-backend --platform managed

# Frontend
cd frontend
gcloud builds submit --tag gcr.io/PROJECT_ID/calendar-frontend
gcloud run deploy --image gcr.io/PROJECT_ID/calendar-frontend --platform managed
```

## 🔧 Environment Variables for Production

### Backend Variables:
```
DEEPSEEK_API_KEY=sk-...
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_CALENDAR_ID=primary
PORT=8000
```

### Frontend Variables:
```
BACKEND_URL=https://your-backend-domain.com
PORT=8501
```

## 🔒 Security Best Practices

1. **Never commit credentials**: Use environment variables
2. **Rotate API keys**: Regularly update DeepSeek and Google credentials
3. **Limit calendar access**: Only grant necessary permissions
4. **Use HTTPS**: Ensure all communication is encrypted
5. **Monitor usage**: Set up alerts for unusual API usage

## 📊 Monitoring and Logging

### Application Monitoring:
- Set up health checks on `/health` endpoint
- Monitor API response times
- Track calendar API quota usage
- Monitor DeepSeek token usage

### Logging Configuration:
```python
# Add to main.py for structured logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🚨 Troubleshooting

### Common Deployment Issues:

1. **Build Failures**:
   - Check Python version (use 3.11+)
   - Verify all dependencies in requirements.txt
   - Check for missing system dependencies

2. **Google Calendar Issues**:
   - Verify service account JSON format
   - Check calendar sharing permissions
   - Ensure Calendar API is enabled

3. **DeepSeek Connection**:
   - Verify API key format
   - Check account billing status
   - Monitor rate limits

4. **Port/Network Issues**:
   - Use `0.0.0.0` host binding for containers
   - Check port configuration
   - Verify CORS settings

### Debug Commands:
```bash
# Test backend health
curl https://your-backend-url/health

# Check backend logs
railway logs # or platform-specific command

# Test frontend connection
curl https://your-frontend-url/_stcore/health
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example:
```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy Backend
      run: railway up --service backend
    - name: Deploy Frontend  
      run: railway up --service frontend
```

## 📈 Scaling Considerations

- **Backend**: Consider Redis for session storage
- **Database**: Add PostgreSQL for persistent data
- **Caching**: Implement API response caching
- **Load Balancing**: Use platform load balancers
- **CDN**: Serve static assets via CDN

## 💰 Cost Optimization

- Use free tiers when available
- Monitor API usage closely
- Implement request caching
- Set up usage alerts
- Consider serverless for variable workloads

## 📞 Support Resources

- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Fly.io Docs](https://fly.io/docs/)
- [Google Calendar API](https://developers.google.com/calendar)
- [DeepSeek API Docs](https://platform.deepseek.com/docs)