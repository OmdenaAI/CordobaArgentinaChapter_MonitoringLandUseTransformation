# Land Use Change Detection Project

Land use change detection and monitoring system in Córdoba, Argentina, using satellite imagery.

## System Requirements

### Software Versions
- Python 3.11.8
- Node.js 18
- Redis 7.0

### Development Environment Setup

### 1. Clone the repository:
```bash
git clone https://github.com/OmdenaAI/CordobaArgentinaChapter_MonitoringLandUseTransformation.git
```

### 2. Navigate to project directory:
```bash
cd CordobaArgentinaChapter_MonitoringLandUseTransformation
```

### 3. Install Python 3.11.8:

#### For MacOS (using pyenv):
```bash
# Install pyenv if you haven't already
brew install pyenv

# Install Python 3.11.8
pyenv install 3.11.8

# Set Python 3.11.8 as local version for this project
pyenv local 3.11.8

# Reload shell configuration
source ~/.zshrc    # If using zsh
# OR
source ~/.bashrc   # If using bash

# Verify installation
python --version  # Should show Python 3.11.8
```

#### For Windows:
```powershell
# Using winget (Windows Package Manager)
winget install Python.Python.3.11

# Or download the installer from official website
# https://www.python.org/downloads/release/python-3117/

# Refresh environment variables (open a new terminal)
# OR run this command in PowerShell:
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verify installation
python --version  # Should show Python 3.11.8
```

### 4. Set up Python virtual environments:

#### Preprocessing Service:
```bash
python -m venv preprocessing_service/venv
source preprocessing_service/venv/bin/activate # Linux/Mac
.\preprocessing_service\venv\Scripts\activate # Windows
```

Install dependencies (if they exist):

```bash
pip install -r preprocessing_service/requirements.txt
```

#### Model Service:
```bash
python -m venv model-service/venv
source model_service/venv/bin/activate # Linux/Mac
.\model_service\venv\Scripts\activate # Windows
```

Install dependencies (if they exist):

```bash
pip install -r model_service/requirements.txt
```

#### API Gateway:
```bash
python -m venv api-gateway/venv
source api_gateway/venv/bin/activate # Linux/Mac
.\api_gateway\venv\Scripts\activate # Windows
```

Install dependencies (if they exist):

```bash
pip install -r api_gateway/requirements.txt
```

#### Queue Service:
```bash
python -m venv queue-service/venv
source queue_service/venv/bin/activate # Linux/Mac
.\queue_service\venv\Scripts\activate # Windows
```

Install dependencies (if they exist):

```bash
pip install -r queue_service/requirements.txt
```

#### Set up Frontend:
```bash
cd frontend
npm install
```

#### Configure Redis:
```bash
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest
```

## Project Structure

```
change_detection_project/
├── preprocessing_service/ # Image preprocessing service
├── model_service/        # Model inference service
├── api_gateway/          # API Gateway (FastAPI)
├── queue_service/        # Queue service (Redis + Celery)
├── frontend/            # Frontend (React)
└── common/              # Shared code between services
```

## Local Development

### Running Services Individually

#### 1. Preprocessing Service:
```bash
cd preprocessing_service
source venv/bin/activate
python src/main.py
```

#### 2. Model Service:
```bash
cd model_service
source venv/bin/activate
python src/main.py
```

#### 3. API Gateway:
```bash
cd api_gateway
source venv/bin/activate
uvicorn src.main:app --reload
```

#### 4. Queue Service:
```bash
cd queue_service
source venv/bin/activate
celery -A src.workers worker --loglevel=info
```

#### 5. Frontend:
```bash
cd frontend
npm run dev
```

### Using Docker Compose

```bash
docker-compose up -d
```

## Code Conventions

- Follow PEP 8 for Python
- ESLint with Airbnb config for JavaScript/TypeScript
- Conventional Commits for commit messages
- Google Style Python Docstrings for documentation

## Git Workflow

1. Create branch from develop:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/feature_name
```

2. Commit changes:
```bash
git add .
git commit -m "feat: description of change"
git push origin feature/feature_name
```
Create PR in GitHub from feature -> develop

## Additional Documentation

- [Development Guide](./docs/development.md)
- [API Documentation](./api-gateway/README.md)
- [Deployment Guide](./docs/deployment.md)

## Contact

For questions or suggestions, contact:
- Tech Lead: [Name](mailto:email@example.com)
- Project Manager: [Name](mailto:email@example.com)

## Available Satellites

![Satellite Constellation](./docs/assets/satellites.png)

## Satellite Data Sources

The project can work with imagery from the following satellites:

| Satellite | Resolution | Revisit Time | Bands | Best Use Case |
|-----------|------------|--------------|--------|---------------|
| Sentinel-2 | 10m, 20m, 60m | 5 days | 13 bands | Land use, agriculture, forest monitoring |
| Landsat 8-9 | 15m, 30m, 100m | 16 days | 11 bands | Historical analysis, long-term changes |
| MODIS | 250m, 500m, 1km | Daily | 36 bands | Large-scale monitoring, rapid changes |
| Planet | 3-5m | Daily | 4 bands | High-resolution monitoring (commercial) |