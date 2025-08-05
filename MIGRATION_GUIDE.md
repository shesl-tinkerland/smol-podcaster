# Smol Podcaster Migration Guide

## Overview

This document describes the migration from the Flask monolith to a modern FastAPI backend with Next.js frontend architecture. The new architecture provides better performance, type safety, and maintainability.

## Architecture Changes

### Before (Flask Monolith)
```
smol-podcaster/
├── web.py              # Flask application
├── smol_podcaster.py   # Main processing script
├── tasks.py            # Celery tasks
├── templates/          # HTML templates
└── requirements.txt    # Python dependencies
```

### After (FastAPI + Next.js)
```
smol-podcaster/
├── backend/
│   ├── app/
│   │   ├── api/        # FastAPI routes
│   │   ├── services/   # Business logic layer
│   │   ├── models/     # Pydantic models
│   │   └── core/       # Core configuration
│   └── requirements.txt
└── frontend/
    ├── app/            # Next.js pages
    ├── components/     # React components
    ├── lib/            # API client
    └── types/          # TypeScript types
```

## Key Improvements

### 1. **Modular Service Architecture**
- Separated concerns into distinct service layers
- Each service handles a specific domain (transcription, AI, episodes, etc.)
- Easier to test and maintain

### 2. **Type Safety**
- Full TypeScript support in frontend
- Pydantic models for request/response validation
- Compile-time error catching

### 3. **Modern UI/UX**
- React-based frontend with Next.js
- Responsive design with Tailwind CSS
- shadcn/ui component library
- Real-time updates with React Query

### 4. **Better Testing**
- Unit tests for all services and routes
- Integration tests for workflows
- React component tests
- E2E tests with Playwright

### 5. **Improved Developer Experience**
- Hot reloading in development
- Better error messages
- Structured logging
- Docker compose for easy setup

## API Endpoints Mapping

| Flask Route | FastAPI Route | Description |
|------------|---------------|-------------|
| `GET /` | `GET /api/v1/episodes/` | List episodes |
| `POST /process` | `POST /api/v1/episodes/` | Create new episode |
| `GET/POST /edit/<name>` | `PATCH /api/v1/episodes/{id}/show-notes` | Update show notes |
| `POST /sync_chapters` | `POST /api/v1/chapters/sync` | Sync chapters |
| N/A | `GET /api/v1/transcripts/{name}` | Get transcript |
| N/A | `GET /api/v1/processing/status/{task_id}` | Check task status |

## Migration Steps

### 1. **Backend Setup**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. **Frontend Setup**

```bash
cd frontend
npm install
npm run dev
```

### 3. **Database Migration**
The new system uses an in-memory database for episodes. For production, configure PostgreSQL:

```python
# backend/app/core/config.py
DATABASE_URL = "postgresql://user:pass@localhost/smol_podcaster"
```

### 4. **Environment Variables**

Create `.env` files:

**Backend (.env)**
```env
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
REPLICATE_API_TOKEN=your_key
REDIS_URL=redis://localhost:6379
```

**Frontend (.env.local)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 5. **Celery Configuration**

The new system uses the same Celery setup but with better task tracking:

```bash
celery -A app.core.celery_app worker --loglevel=info
```

## Feature Parity Checklist

- [x] Episode upload (file or URL)
- [x] Podcast transcription
- [x] AI-generated content (chapters, show notes, writeup)
- [x] Show notes editing
- [x] Chapter synchronization
- [x] Task status tracking
- [x] Episode listing
- [x] File system storage compatibility

## New Features

1. **Real-time Status Updates**: Task progress is tracked and can be queried
2. **Better Error Handling**: Detailed error messages and graceful failures
3. **API Documentation**: Auto-generated at `/docs`
4. **Type-safe API Client**: Frontend knows exact response shapes
5. **Responsive Design**: Works on mobile devices

## Testing

### Run Backend Tests
```bash
cd backend
pytest
```

### Run Frontend Tests
```bash
cd frontend
npm run test        # Unit tests
npm run test:e2e    # E2E tests
npm run typecheck   # TypeScript checks
```

## Deployment

### Using Docker Compose
```bash
docker-compose up
```

### Production Considerations
1. Use PostgreSQL instead of in-memory storage
2. Configure Redis for production
3. Set up proper logging
4. Use environment-specific configs
5. Enable CORS for your domain only
6. Set up SSL/TLS
7. Configure rate limiting

## Troubleshooting

### Common Issues

1. **TypeScript Errors**
   - Run `npm install` to ensure all dependencies are installed
   - Check that `tsconfig.json` has correct module resolution

2. **API Connection Issues**
   - Ensure backend is running on port 8000
   - Check CORS configuration
   - Verify API URL in frontend config

3. **Celery Tasks Not Running**
   - Check Redis is running
   - Verify Celery worker is started
   - Check task logs for errors

4. **File Upload Issues**
   - Ensure upload directories exist
   - Check file permissions
   - Verify max file size settings

## Code Examples

### Creating a New Service

```python
# backend/app/services/my_service.py
class MyService:
    async def process_data(self, data: str) -> str:
        # Business logic here
        return processed_data
```

### Adding a New API Endpoint

```python
# backend/app/api/v1/my_endpoint.py
@router.post("/process")
async def process(data: DataModel) -> ResponseModel:
    service = MyService()
    result = await service.process_data(data.content)
    return ResponseModel(result=result)
```

### Creating a React Component

```typescript
// frontend/components/MyComponent.tsx
interface MyComponentProps {
  data: string;
}

export function MyComponent({ data }: MyComponentProps) {
  return <div>{data}</div>;
}
```

## Performance Optimizations

1. **Caching**: React Query caches API responses
2. **Lazy Loading**: Components load on demand
3. **Async Processing**: All I/O operations are async
4. **Connection Pooling**: Database connections are pooled
5. **Static Generation**: Next.js pre-renders pages

## Security Considerations

1. **Input Validation**: All inputs validated with Pydantic
2. **SQL Injection**: Using ORM prevents SQL injection
3. **XSS Prevention**: React escapes content by default
4. **CORS**: Configured for specific origins
5. **Rate Limiting**: Can be added with FastAPI middleware
6. **Authentication**: Can be added with JWT tokens

## Future Enhancements

1. User authentication and multi-tenancy
2. Real-time WebSocket updates
3. Advanced search functionality
4. Batch processing
5. Analytics dashboard
6. Plugin system for custom processors

## Support

For issues or questions:
1. Check the error logs
2. Review this documentation
3. Check the test files for examples
4. Open an issue on GitHub