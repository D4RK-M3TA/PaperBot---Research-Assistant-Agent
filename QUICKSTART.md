# PaperBot Quick Start Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis
- Node.js 18+ (for frontend)
- Docker & Docker Compose (optional)

## Quick Start (5 minutes)

### 1. Clone and Setup

```bash
cd PaperBot
cp .env.example .env
# Edit .env with your settings (at minimum, set SECRET_KEY)
```

### 2. Install Dependencies

```bash
# Python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### 3. Database Setup

```bash
# Create database (PostgreSQL)
createdb paperbot  # Or use psql

# Run migrations
python manage.py migrate

# Setup default models
python manage.py setup_models

# Create superuser
python manage.py createsuperuser
```

### 4. Start Services

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A paperbot worker -l info

# Terminal 3: Frontend
cd frontend
npm run dev
```

### 5. Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin: http://localhost:8000/admin

## Docker Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## First Steps

1. **Login/Register**: Use the frontend or API to create an account
2. **Create Workspace**: Create a workspace for your documents
3. **Upload PDF**: Upload a research paper PDF
4. **Wait for Processing**: Check document status (should go: uploaded → processing → indexed)
5. **Query**: Ask questions about your documents
6. **Summarize**: Generate summaries of multiple documents

## API Examples

### Get JWT Token

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

### Upload Document

```bash
curl -X POST http://localhost:8000/api/documents/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "workspace_id=1" \
  -F "file=@paper.pdf" \
  -F "title=Research Paper"
```

### Query Documents

```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": 1,
    "query": "What is the main contribution?",
    "top_k": 5
  }'
```

## Configuration

### Required Environment Variables

Minimum `.env` configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=paperbot
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Optional (for LLM features)

```env
OPENAI_API_KEY=your-openai-key
# OR
ANTHROPIC_API_KEY=your-anthropic-key
```

## Troubleshooting

### Database Connection Error

- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify database exists: `psql -l | grep paperbot`

### Celery Not Processing

- Check Redis is running: `redis-cli ping`
- Verify Celery worker is running: `celery -A paperbot worker -l info`
- Check task status in Django admin

### Embeddings Not Working

- Run: `python manage.py setup_models`
- Check embedding model is active in admin
- Verify `EMBEDDING_MODEL` in settings

### Frontend Not Connecting

- Check backend is running on port 8000
- Verify CORS settings in `settings.py`
- Check browser console for errors

## Next Steps

- Read `README.md` for full documentation
- Check `PROJECT_STRUCTURE.md` for architecture
- Explore `notebooks/rag_demo.ipynb` for RAG examples
- Review `openapi.yaml` for API documentation





