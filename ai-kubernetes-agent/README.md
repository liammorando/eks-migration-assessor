# AI Kubernetes Agent

An AI-powered Kubernetes troubleshooting agent that investigates cluster issues and provides root cause analysis with suggested fixes.

## Architecture

```
Frontend (Next.js)
    ↓
FastAPI Backend (Orchestrator)
    ↓
Kubernetes Investigation Layer
    ↓
AI Kubernetes Agent
    ↓
LLM Reasoning (OpenRouter via InsForge)
    ↓
Root Cause + Suggested Fix
    ↓
Frontend Diagnosis
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend development)

### Running with Docker Compose

```bash
docker compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/health

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure your environment variables
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
cp .env.example .env  # Configure your environment variables
npm run dev
```

## Project Structure

```
ai-kubernetes-agent/
├── backend/
│   ├── api/              # API routes
│   ├── core/             # Core configuration, logging
│   ├── kubernetes/       # Kubernetes inspection logic
│   ├── ai/               # AI agent logic
│   ├── services/         # Business logic services
│   ├── models/           # Pydantic models
│   ├── main.py           # FastAPI app entry point
│   ├── requirements.txt  # Python dependencies
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # React components
│   │   ├── services/     # API services
│   │   ├── hooks/        # Custom React hooks
│   │   └── types/        # TypeScript types
│   ├── package.json
│   ├── Dockerfile
│   └── .env
├── docs/
├── prompts/
├── docker-compose.yml
└── README.md
```

## Environment Variables

### Backend (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM access | - |
| `OPENROUTER_MODEL` | Model to use for AI reasoning | `anthropic/claude-3.5-sonnet` |
| `KUBECONFIG_PATH` | Path to kubeconfig file | - |

### Frontend (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |

## API Endpoints

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "ai-kubernetes-agent"
}
```

### Investigate Cluster (Not Implemented)

```
POST /api/v1/investigate
```

## Tech Stack

### Backend
- FastAPI
- Python 3.12+
- Uvicorn
- Pydantic
- Loguru
- HTTPX

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS 3.4
- Axios
- React Query (TanStack Query)

### Infrastructure
- Docker
- Docker Compose

## Development Notes

- The backend uses a modular structure with clear separation of concerns
- The frontend uses React Query for server state management
- CORS is configured for local development
- Logging is configured with Loguru (console + file)
- Environment variables are loaded via Pydantic Settings

## Next Steps

- Implement Kubernetes inspection layer (`backend/kubernetes/`)
- Implement AI agent with OpenRouter integration (`backend/ai/`)
- Add investigation API endpoints
- Build diagnosis UI components
- Add authentication
- Add real-time updates via WebSocket