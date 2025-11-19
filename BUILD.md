# DealFlow AI - Build Guide

This document provides instructions for building and running the DealFlow AI platform.

## Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 20.x or higher
- **Docker**: Latest version (optional, for containerized deployment)
- **PostgreSQL**: 15 or higher (for local development)
- **Redis**: 7 or higher (for worker queue)

## Project Structure

```
dealflow-ai/
├── apps/
│   ├── backend/         # FastAPI backend service
│   ├── frontend/        # Next.js frontend application
│   └── worker/          # Python async worker service
├── services/
│   ├── data_ingestion/  # Data pipeline services
│   ├── scoring_engine/  # ML scoring engine
│   └── workflow_automation/
├── infrastructure/
│   ├── docker/          # Docker configurations
│   ├── k8s/            # Kubernetes manifests
│   └── terraform/      # Infrastructure as Code
├── configs/            # Configuration files
└── docs/              # Documentation
```

## Quick Start with Bootstrap Script

The easiest way to set up the development environment:

```bash
# Run the bootstrap script
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
```

This will:
- Create a Python virtual environment at `.venv/`
- Install backend and worker dependencies
- Install frontend Node.js dependencies

## Manual Setup

### 1. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install backend with dev dependencies
pip install -e apps/backend[dev]

# Run backend
cd apps/backend
uvicorn dealflow_backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs available at: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd apps/frontend

# Install dependencies (use npm ci for consistent installs)
npm ci

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### 3. Worker Setup

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Install worker with dev dependencies
pip install -e apps/worker[dev]

# Run worker
cd apps/worker
python -m dealflow_worker.main
```

## Docker Setup

### Using Docker Compose

The recommended way to run the entire stack:

```bash
# Navigate to docker directory
cd infrastructure/docker

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Services will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### Building Individual Images

```bash
# Build backend
docker build -f infrastructure/docker/backend.Dockerfile -t dealflow-backend .

# Build frontend
docker build -f infrastructure/docker/frontend.Dockerfile -t dealflow-frontend .

# Build worker
docker build -f infrastructure/docker/worker.Dockerfile -t dealflow-worker .
```

## Environment Configuration

### Backend Environment

Copy the example environment file and configure:

```bash
cp configs/env/backend.env.example configs/env/backend.env
```

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `API_KEY`: API authentication key

### Frontend Environment

```bash
cp configs/env/frontend.env.example configs/env/frontend.env
```

Key variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_ENV`: Environment (development/production)

### Worker Environment

```bash
cp configs/env/worker.env.example configs/env/worker.env
```

## Build for Production

### Frontend Production Build

```bash
cd apps/frontend
npm run build
npm run start
```

### Backend Production

```bash
# Install production dependencies only
pip install -e apps/backend

# Run with production settings
uvicorn dealflow_backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Development Scripts

Several helper scripts are available in the `scripts/` directory:

```bash
# Format code
./scripts/format.sh

# Lint code
./scripts/lint.sh
```

## Testing

### Backend Tests

```bash
cd apps/backend
pytest tests/
```

### Frontend Tests

```bash
cd apps/frontend
npm run test
```

## Common Issues

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Kill the process or use a different port
```

### Python Module Not Found

Ensure you've activated the virtual environment and installed the packages in editable mode:

```bash
source .venv/bin/activate
pip install -e apps/backend[dev]
```

### Node Module Errors

Clear node_modules and reinstall:

```bash
cd apps/frontend
rm -rf node_modules package-lock.json
npm install
```

## Clean Build

To start fresh and remove all build artifacts:

```bash
# Remove Python build artifacts
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove Node.js build artifacts
cd apps/frontend
rm -rf node_modules .next dist

# Rebuild from scratch
cd ../..
./scripts/bootstrap.sh
```

## Additional Resources

- [Architecture Documentation](./docs/architecture/v2/)
- [API Documentation](http://localhost:8000/docs) (when backend is running)
- [Product Specifications](./docs/product/)
- [UX/UI Guidelines](./docs/ux/)

## Support

For issues or questions:
1. Check the [docs/](./docs/) directory
2. Review existing issues in the repository
3. Contact the development team
