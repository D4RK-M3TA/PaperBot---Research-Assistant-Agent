# ✅ PaperBot Setup Complete!

## What's Been Installed & Configured

### ✅ ML Dependencies (RAG Features)
- **sentence-transformers** - For creating embeddings
- **faiss-cpu** - For vector similarity search
- **numpy** - Required dependency
- **torch** - PyTorch (installed with sentence-transformers)

### ✅ LLM Clients (Q/A Features)
- **openai** - OpenAI API client
- **anthropic** - Anthropic/Claude API client

### ✅ Database Setup
- **SQLite** - Currently configured and working
- **PostgreSQL** - Available on port 5432 (requires password setup)
- **psycopg2-binary** - PostgreSQL adapter installed

### ✅ Redis Setup
- **Redis** - Available on port 6379 (via Docker or system)
- **celery** - Task queue installed

### ✅ Django Configuration
- All migrations applied
- Default embedding model created
- Generation models created (GPT-4, GPT-3.5, Claude)
- **Superuser created!**
  - Username: `admin`
  - Password: `admin123`
  - Email: `admin@paperbot.com`

## Quick Start

### Run the Server
```bash
cd /home/d4rk_m3ta/Desktop/PaperBot
source venv/bin/activate
USE_SQLITE=True python manage.py runserver
```

### Access Points
- **API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **Login**: admin / admin123

### Test RAG Features
Once you upload a PDF and it's processed, you can:
- Query documents: `POST /api/query/`
- Summarize: `POST /api/summarize/`
- Chat: `POST /api/chat/`

## PostgreSQL Setup (Optional)

If you want to use PostgreSQL instead of SQLite:

1. **Create database**:
   ```bash
   # Option 1: With password
   PGPASSWORD=your_password psql -h localhost -U postgres -c "CREATE DATABASE paperbot;"
   
   # Option 2: As postgres user
   sudo -u postgres psql -c "CREATE DATABASE paperbot;"
   ```

2. **Update .env** (or set environment variables):
   ```env
   USE_SQLITE=False
   DB_NAME=paperbot
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

## Redis Setup (For Celery)

Redis is already running on port 6379. To use Celery for async tasks:

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A paperbot worker -l info
```

## Next Steps

1. **Set API Keys** (in .env or environment):
   ```env
   OPENAI_API_KEY=your_key_here
   # OR
   ANTHROPIC_API_KEY=your_key_here
   ```

2. **Upload a PDF**:
   - Login to admin panel
   - Create a workspace
   - Upload a PDF document
   - Wait for processing (or check Celery worker)

3. **Test RAG Query**:
   ```bash
   curl -X POST http://localhost:8000/api/query/ \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"workspace_id": 1, "query": "What is this paper about?"}'
   ```

## Verification

All dependencies verified:
- ✅ sentence-transformers
- ✅ faiss-cpu
- ✅ openai
- ✅ anthropic
- ✅ Django system check: No issues

## Notes

- Currently using SQLite for quick setup
- PostgreSQL available but requires password configuration
- Redis available on port 6379
- All ML/LLM dependencies installed and working
- Superuser ready to use





