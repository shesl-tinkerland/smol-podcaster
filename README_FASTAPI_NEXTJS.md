# Smol Podcaster - Modern Architecture

A modern podcast post-production platform built with FastAPI and Next.js, designed to automate transcription, generate show notes, and create content for podcasters.

## 🚀 Features

- **Audio Transcription**: Automatic transcription with speaker diarization using Whisper
- **AI-Powered Content Generation**: 
  - Chapter markers with timestamps
  - Show notes with entity extraction
  - Content writeups
  - Title suggestions
  - Social media posts
- **Chapter Synchronization**: Align timestamps between audio and video versions
- **Modern UI**: Responsive interface built with Next.js and Tailwind CSS
- **Real-time Processing**: Track task progress with Celery and Redis
- **Type Safety**: Full TypeScript support with validated API contracts

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Next.js      │────▶│    FastAPI      │────▶│     Celery      │
│    Frontend     │     │    Backend      │     │     Worker      │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                         │
                               ▼                         ▼
                        ┌─────────────┐          ┌─────────────┐
                        │   Redis     │          │  AI APIs    │
                        │   Cache     │          │ (OpenAI,    │
                        └─────────────┘          │ Anthropic)  │
                                                 └─────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- Redis
- Docker (optional)

## 🛠️ Installation

### Option 1: Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/FanaHOVA/smol-podcaster.git
cd smol-podcaster

# Create environment files
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# Add your API keys to backend/.env
# OPENAI_API_KEY=your_key
# ANTHROPIC_API_KEY=your_key
# REPLICATE_API_TOKEN=your_key

# Start all services
docker-compose up
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
export REPLICATE_API_TOKEN=your_key

# Start Redis (required for Celery)
redis-server

# Start Celery worker (in a new terminal)
celery -A app.core.celery_app worker --loglevel=info

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🎯 Usage

1. **Access the application**: Open http://localhost:3000 in your browser

2. **Create a new episode**:
   - Upload an audio file or provide a URL
   - Set the number of speakers
   - Choose processing options
   - Click "Create Artifacts"

3. **Monitor progress**: The episode will be processed in the background

4. **Edit show notes**: Once processing is complete, edit the generated show notes

5. **Sync chapters**: Synchronize chapter timestamps between audio and video versions

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest                          # Run all tests
pytest tests/test_services.py   # Run specific test file
pytest -v                       # Verbose output
pytest --cov=app               # With coverage
```

### Frontend Tests

```bash
cd frontend
npm run test                    # Run unit tests
npm run test:watch             # Watch mode
npm run test:coverage          # With coverage
npm run typecheck              # TypeScript type checking
```

### E2E Tests

```bash
cd frontend
npx playwright install         # Install browsers (first time)
npm run test:e2e              # Run E2E tests
npm run test:e2e:ui          # Run with UI
```

## 📚 API Documentation

When the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Episodes
- `POST /api/v1/episodes/` - Create new episode
- `GET /api/v1/episodes/` - List all episodes
- `GET /api/v1/episodes/{id}` - Get episode details
- `PATCH /api/v1/episodes/{id}/show-notes` - Update show notes

#### Transcripts
- `GET /api/v1/transcripts/{name}` - Get clean transcript
- `GET /api/v1/transcripts/{name}/raw` - Get raw transcript data

#### Processing
- `GET /api/v1/processing/status/{task_id}` - Check task status
- `POST /api/v1/processing/retry/{task_id}` - Retry failed task

#### Chapters
- `POST /api/v1/chapters/sync` - Synchronize chapters

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
REPLICATE_API_TOKEN=r8_...

# Models
GPT_MODEL=gpt-4o-2024-08-06
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🚢 Deployment

### Railway/Render/Heroku

1. Set environment variables in platform dashboard
2. Update `CORS_ORIGINS` to include your domain
3. Use provided Dockerfiles or buildpacks

### Self-Hosted

1. Set up reverse proxy (nginx/caddy)
2. Configure SSL certificates
3. Set up process managers (systemd/supervisor)
4. Configure PostgreSQL for production

## 📂 Project Structure

```
smol-podcaster/
├── backend/
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configs
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── tests/          # Test files
│   └── requirements.txt
├── frontend/
│   ├── app/                # Next.js pages
│   ├── components/         # React components
│   ├── lib/                # Utilities
│   ├── types/              # TypeScript types
│   └── package.json
└── docker-compose.yml
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for the Latent Space podcast
- Uses OpenAI GPT and Anthropic Claude for content generation
- Transcription powered by Replicate's Whisper implementation

## 💡 Tips

- For better transcription accuracy, use high-quality audio files
- Adjust the number of speakers for optimal diarization
- Edit generated content to match your style
- Use chapter sync when you have both audio and video versions
- Monitor Celery logs for processing insights

## 🐛 Troubleshooting

### Common Issues

1. **Connection refused on port 8000**
   - Ensure FastAPI backend is running
   - Check if another service is using the port

2. **Celery tasks not processing**
   - Verify Redis is running
   - Check Celery worker logs
   - Ensure API keys are set correctly

3. **TypeScript errors in frontend**
   - Run `npm install` to ensure dependencies are installed
   - Check that all imports are correct

4. **CORS errors**
   - Update `CORS_ORIGINS` in backend config
   - Ensure frontend is using correct API URL

## 📞 Support

- Open an issue on GitHub
- Check existing issues for solutions
- Review test files for usage examples