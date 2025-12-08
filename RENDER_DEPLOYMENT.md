# Render Deployment Configuration Guide

This guide provides the exact configuration values needed to deploy PaperBot on Render.

## 1. Root Directory (Optional)
**Leave this field BLANK** - Your Django project is at the repository root.

**Note**: The project includes a `runtime.txt` file that specifies Python 3.11.9. Render will automatically detect and use this version.

## 2. Build Command
```
pip install -r requirements.txt
```

**Note**: Gunicorn is now included in requirements.txt, so no need to install separately.

## 3. Start Command
```
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn paperbot.wsgi:application --bind 0.0.0.0:$PORT
```

**Important**: Render automatically sets the `$PORT` environment variable, so we use `$PORT` instead of hardcoding port 8000.

## 4. Environment Variables

Add the following environment variables in Render's Environment Variables section:

### Required - Core Django Settings
```
SECRET_KEY=<generate-a-secure-random-key>
DEBUG=False
ALLOWED_HOSTS=<your-render-app-url>.onrender.com
```

### Required - Database (PostgreSQL)
You'll need to create a PostgreSQL database service on Render first, then use its connection details:
```
DB_NAME=<from-render-postgres-service>
DB_USER=<from-render-postgres-service>
DB_PASSWORD=<from-render-postgres-service>
DB_HOST=<from-render-postgres-service>
DB_PORT=5432
```

### Required - Redis (for Celery)
You'll need to create a Redis service on Render first, then use its connection details:
```
REDIS_URL=<from-render-redis-service>
CELERY_BROKER_URL=<from-render-redis-service>
CELERY_RESULT_BACKEND=<from-render-redis-service>
```

### Required - LLM API Keys (at least one)
```
OPENAI_API_KEY=<your-openai-api-key>
# OR
ANTHROPIC_API_KEY=<your-anthropic-api-key>
LLM_PROVIDER=openai  # or 'anthropic'
```

### Optional - Vector DB Configuration
```
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=/opt/render/project/src/vector_db
```

### Optional - Embedding Model
```
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Optional - AWS S3 (for file storage)
If you want to use S3 for media files instead of local storage:
```
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_STORAGE_BUCKET_NAME=paperbot-documents
AWS_S3_REGION_NAME=us-east-1
```

### Optional - Rate Limiting
```
RATE_LIMIT_INGESTION=10
RATE_LIMIT_GENERATION=100
```

## 5. Additional Setup Steps

### Step 1: Create PostgreSQL Database
1. In Render dashboard, create a new **PostgreSQL** service
2. Copy the connection details (Internal Database URL)
3. Use these values for the `DB_*` environment variables

### Step 2: Create Redis Service
1. In Render dashboard, create a new **Redis** service
2. Copy the connection URL
3. Use this URL for `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND`

### Step 3: Create Celery Worker Service (Optional but Recommended)
Since your app uses Celery for async tasks, you should also deploy a Celery worker:

**For Celery Worker Service:**
- **Root Directory**: (leave blank)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `celery -A paperbot worker -l info`
- **Environment Variables**: Same as your main web service

**For Celery Beat Service** (if you need scheduled tasks):
- **Root Directory**: (leave blank)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `celery -A paperbot beat -l info`
- **Environment Variables**: Same as your main web service

### Step 4: Create Superuser
After deployment, you'll need to create a superuser. You can do this via Render's shell:
```bash
python manage.py createsuperuser
```

## 6. Important Notes

1. **Static Files**: The `collectstatic` command in the start command will collect static files to `staticfiles/` directory. Make sure your Django settings are configured correctly.

2. **Media Files**: By default, media files are stored locally. For production, consider using AWS S3 by configuring the AWS environment variables.

3. **Vector DB Storage**: The vector database files are stored locally. On Render, these will be ephemeral (lost on restart). Consider using a persistent storage solution or migrating to a cloud vector DB service.

4. **Port**: Always use `$PORT` environment variable in your start command - Render sets this automatically.

5. **Health Checks**: Render will automatically check your service health. Make sure your app responds to requests on the root URL or configure a health check endpoint.

## 7. Quick Reference Checklist

- [ ] Web Service created with correct build/start commands
- [ ] PostgreSQL database service created
- [ ] Redis service created
- [ ] All environment variables set
- [ ] Celery worker service created (optional)
- [ ] Celery beat service created (optional)
- [ ] Superuser created
- [ ] Test the deployment

## Troubleshooting

- **Build fails**: Check that all dependencies in requirements.txt are compatible
- **App crashes**: Check Render logs for errors, verify all environment variables are set
- **Database connection fails**: Verify DB_* environment variables match your PostgreSQL service
- **Celery tasks not working**: Ensure Redis is configured and Celery worker service is running
