# Render Deployment Configuration Guide

This guide provides the exact configuration values needed to deploy PaperBot on Render.

## 1. Root Directory (Optional)
**Leave this field BLANK** - Your Django project is at the repository root.

**Note**: The project includes a `.python-version` file that specifies Python 3.11. Render will automatically detect and use Python 3.11 (latest patch version).

## 2. Build Command
```
bash build.sh
```

**OR manually:**
```
pip install "numpy==1.26.4" && pip install -r requirements.txt && cd frontend && npm install && npm run build && cd ..
```

**Important**: 
- We install numpy first to ensure it's installed before other packages that might pull in numpy 2.x
- This ensures torch 2.1.2 compatibility (torch requires numpy < 2.0)
- The frontend is built using Vite, which creates static files in `frontend/dist/`
- **CRITICAL**: Make sure your Render dashboard build command includes the frontend build step!
- Render should have Node.js available automatically, but if build fails, check Node.js version in Render settings

## 3. Start Command
```
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn paperbot.wsgi:application -c gunicorn_config.py
```

**Important**: 
- Uses a custom gunicorn config file optimized for memory-constrained environments
- Uses only 1 worker to reduce memory usage (important for Render's free tier)
- Increased timeout to handle model loading
- Render automatically sets the `$PORT` environment variable in the config file

## 4. Environment Variables

Add the following environment variables in Render's Environment Variables section:

### Required - Core Django Settings
```
SECRET_KEY=<generate-a-secure-random-key>
DEBUG=False
ALLOWED_HOSTS=<your-render-app-url>.onrender.com
```

### Required - Database (PostgreSQL)
**CRITICAL**: You MUST create a PostgreSQL database service on Render first, then set these environment variables.

**Steps:**
1. In Render dashboard, create a new **PostgreSQL** service
2. After creation, go to the PostgreSQL service's "Info" tab
3. Copy the connection details. You'll see fields like:
   - **Internal Database URL** (or connection string)
   - **Hostname** (NOT localhost!)
   - **Database Name**
   - **Username**
   - **Password**
   - **Port** (usually 5432)

**Set these environment variables in your Web Service:**
```
DB_NAME=<database-name-from-render>
DB_USER=<username-from-render>
DB_PASSWORD=<password-from-render>
DB_HOST=<hostname-from-render>  # IMPORTANT: This is NOT localhost!
DB_PORT=5432
```

**⚠️ IMPORTANT**: 
- `DB_HOST` must be the hostname provided by Render (e.g., `dpg-xxxxx-a.oregon-postgres.render.com`)
- DO NOT use `localhost` or `127.0.0.1` for `DB_HOST` - this will cause connection errors!
- The hostname is different for Internal vs External connections - use the **Internal** hostname for services in the same region

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
2. After creation, go to the PostgreSQL service's "Info" tab
3. Copy the connection details:
   - **Hostname** (use the Internal hostname, not External)
   - **Database Name**
   - **Username**
   - **Password**
   - **Port** (usually 5432)
4. Set these as environment variables in your Web Service (see section 4 above)
5. **VERIFY**: Make sure `DB_HOST` is NOT set to `localhost` - it must be the Render PostgreSQL hostname!

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

2. **Frontend**: The frontend is built during the build process and served by Django at the root URL (`/`). The React app will be available at your main domain.

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

- **Python version wrong**: Ensure `.python-version` file exists in root with `3.11`. Render will use Python 3.11 automatically.
- **Build fails with numpy/faiss errors**: This usually means Python 3.13 is being used. Check that `.python-version` file exists and contains `3.11`.
- **Build command error**: Make sure your build command in Render dashboard is exactly `pip install "numpy==1.26.4" && pip install -r requirements.txt`.
- **Build fails**: Check that all dependencies in requirements.txt are compatible
- **App crashes**: Check Render logs for errors, verify all environment variables are set
- **Database connection fails with "Connection refused"**: 
  - ⚠️ **MOST COMMON ISSUE**: Check that `DB_HOST` environment variable is set to the Render PostgreSQL hostname (NOT `localhost` or `127.0.0.1`)
  - Verify all `DB_*` environment variables are set correctly
  - Make sure you're using the **Internal** hostname from your PostgreSQL service (not External)
  - Ensure your PostgreSQL service is running and healthy
  - Check that your Web Service and PostgreSQL service are in the same region
- **Celery tasks not working**: Ensure Redis is configured and Celery worker service is running
