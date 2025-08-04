# Smol Podcaster - FastAPI + Next.js Version

A modern podcast transcription and processing application built with FastAPI backend and Next.js frontend.

## Features

- 🎙️ Audio transcription with speaker diarization
- 📝 AI-powered chapter generation, show notes, and writeups
- 🎬 Video chapter synchronization
- 💬 Title and tweet suggestions
- 🔄 Async processing with Celery
- 🎨 Modern UI with Tailwind CSS and ShadCN components
- 📊 Real-time processing status updates

## Architecture

### Backend (FastAPI)
- **API Layer**: RESTful endpoints for episodes, transcripts, processing, and chapters
- **Service Layer**: Modular services for AI, transcription, episodes, and chapter sync
- **Task Queue**: Celery for async processing
- **Storage**: PostgreSQL for metadata, Redis for caching/queue

### Frontend (Next.js)
- **TypeScript**: Full type safety
- **Tailwind CSS**: Utility-first styling
- **ShadCN UI**: Reusable component library
- **React Query**: Data fetching and caching

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key
- Anthropic API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/FanaHOVA/smol-podcaster.git
cd smol-podcaster
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Start the application:
```bash
docker-compose up
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests:
```bash
pytest
pytest -m integration  # Integration tests only
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Type checking:
```bash
npm run typecheck
```

## API Endpoints

### Episodes
- `GET /api/v1/episodes` - List all episodes
- `POST /api/v1/episodes` - Create new episode
- `GET /api/v1/episodes/{id}` - Get episode details
- `PATCH /api/v1/episodes/{id}/show-notes` - Update show notes

### Transcripts
- `GET /api/v1/transcripts/{episode_name}` - Get clean transcript
- `GET /api/v1/transcripts/{episode_name}/raw` - Get raw transcript data

### Processing
- `GET /api/v1/processing/status/{task_id}` - Get processing status
- `POST /api/v1/processing/retry/{task_id}` - Retry failed task

### Chapters
- `POST /api/v1/chapters/sync` - Sync video chapters

## Project Structure

```
smol-podcaster/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # API endpoints
│   │   ├── core/          # Core configuration and tasks
│   │   ├── models/        # Pydantic models
│   │   ├── services/      # Business logic
│   │   └── tests/         # Unit and integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/               # Next.js app directory
│   ├── components/        # React components
│   ├── lib/               # Utilities and API client
│   ├── types/             # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Testing

### Backend Tests
```bash
cd backend
pytest                    # All tests
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
```

### Frontend Tests
```bash
cd frontend
npm run typecheck        # TypeScript type checking
```

## Production Deployment

1. Update environment variables for production
2. Build production images:
```bash
docker-compose -f docker-compose.prod.yml build
```
3. Deploy using your preferred orchestration tool (Kubernetes, ECS, etc.)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `DATABASE_URL` | PostgreSQL connection string | Local default |
| `REDIS_URL` | Redis connection string | Local default |
| `SECRET_KEY` | Application secret key | Dev default |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[MIT License](LICENSE.md)