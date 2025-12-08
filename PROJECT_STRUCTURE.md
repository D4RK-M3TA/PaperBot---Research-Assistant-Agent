# PaperBot Project Structure

## Directory Layout

```
PaperBot/
├── paperbot/                    # Django project root
│   ├── __init__.py             # Celery app initialization
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py                 # WSGI application
│   └── celery.py               # Celery configuration
│
├── core/                        # Core app (models, auth, workspaces)
│   ├── models.py               # User, Workspace, Document, Chunk, etc.
│   ├── serializers.py          # DRF serializers
│   ├── views.py                # Auth and workspace views
│   ├── admin.py                # Django admin configuration
│   ├── middleware.py           # Audit logging middleware
│   ├── urls.py                 # Core app URLs
│   └── management/
│       └── commands/
│           └── setup_models.py # Setup command for default models
│
├── api/                         # API app (document processing, RAG, chat)
│   ├── views.py                # API viewsets and endpoints
│   ├── serializers.py          # API request/response serializers
│   ├── utils.py                # PDFProcessor, EmbeddingService, LLMService
│   ├── tasks.py                # Celery tasks for async processing
│   ├── urls.py                 # API URLs
│   └── tests.py                # API tests
│
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── App.jsx             # Main app component
│   │   ├── App.css             # App styles
│   │   ├── main.jsx            # Entry point
│   │   └── index.css           # Global styles
│   ├── index.html              # HTML template
│   ├── package.json            # NPM dependencies
│   ├── vite.config.js          # Vite configuration
│   └── Dockerfile              # Frontend Docker image
│
├── notebooks/                   # Jupyter notebooks
│   └── rag_demo.ipynb          # RAG demonstration notebook
│
├── docker-compose.yml           # Docker Compose configuration
├── Dockerfile.backend           # Backend Docker image
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── Makefile                     # Make commands
├── openapi.yaml                 # OpenAPI specification
├── README.md                    # Project documentation
└── PROJECT_STRUCTURE.md         # This file
```

## Key Components

### Models (core/models.py)

- **User**: Custom user model extending AbstractUser
- **Workspace**: User workspaces for organizing documents
- **Document**: PDF document metadata and status tracking
- **Chunk**: Text chunks extracted from documents
- **EmbeddingModel**: Versioned embedding model metadata
- **ChunkEmbedding**: Embedding vectors for chunks
- **GenerationModel**: Versioned LLM generation model metadata
- **ChatSession**: Chat sessions for iterative Q/A
- **ChatMessage**: Messages in chat sessions with citations
- **PipelineRun**: Track pipeline execution runs
- **AuditLog**: Audit log for all user actions

### API Endpoints

#### Authentication (`/api/auth/`)
- `POST /api/auth/token/` - Obtain JWT token
- `POST /api/auth/token/refresh/` - Refresh token
- `POST /api/auth/users/register/` - Register user
- `GET /api/auth/users/me/` - Get current user

#### Documents (`/api/documents/`)
- `POST /api/documents/upload/` - Upload PDF (triggers async processing)
- `GET /api/documents/` - List documents

#### RAG (`/api/`)
- `POST /api/query/` - RAG-based Q/A with citations
- `POST /api/summarize/` - Multi-document summarization

#### Chat (`/api/chat/`)
- `POST /api/chat/` - Create chat session
- `GET /api/chat/` - List chat sessions
- `POST /api/chat/{id}/message/` - Send message in session

### Celery Tasks (api/tasks.py)

- **process_document**: Async PDF processing pipeline
  - Extract text from PDF
  - Chunk text
  - Create embeddings
  - Index in vector DB
- **reindex_workspace**: Reindex all documents in a workspace

### Utility Classes (api/utils.py)

- **PDFProcessor**: PDF text extraction and chunking
- **EmbeddingService**: Embedding creation and vector search
- **LLMService**: LLM interactions for Q/A and summarization

## Data Flow

### Document Upload Flow

1. User uploads PDF via `/api/documents/upload/`
2. Document record created with status 'uploaded'
3. Celery task `process_document` triggered
4. Task extracts text → chunks → embeddings → indexes
5. Document status updated through pipeline stages

### RAG Query Flow

1. User sends query to `/api/query/`
2. Query embedded using EmbeddingService
3. Similar chunks retrieved from vector DB
4. LLM called with context chunks
5. Answer + citations returned

### Chat Flow

1. User creates chat session
2. Messages stored with conversation history
3. Each message triggers RAG query
4. Context maintained across messages
5. Citations tracked per message

## Configuration

### Environment Variables

See `.env.example` for all configuration options.

Key variables:
- Database: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`
- Redis: `REDIS_URL`, `CELERY_BROKER_URL`
- LLM: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- Embeddings: `EMBEDDING_MODEL`
- Vector DB: `VECTOR_DB_TYPE`, `VECTOR_DB_PATH`

## Deployment

### Docker Compose

Services:
- `db`: PostgreSQL database
- `redis`: Redis for Celery
- `backend`: Django application
- `celery`: Celery worker
- `celery-beat`: Celery beat scheduler
- `frontend`: React frontend

### Local Development

1. Install dependencies: `pip install -r requirements.txt`
2. Run migrations: `python manage.py migrate`
3. Setup models: `python manage.py setup_models`
4. Run server: `python manage.py runserver`
5. Run worker: `celery -A paperbot worker -l info`

## Testing

Run tests: `python manage.py test`

Test coverage:
- Document upload
- Authentication
- Query endpoints
- Summarization

## Next Steps

1. Set up environment variables
2. Run migrations
3. Create superuser
4. Setup default models
5. Upload test documents
6. Test RAG queries



