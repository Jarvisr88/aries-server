# Insurance System Deployment Guide
Version: 2024-12-19_18-47

## Overview
This guide provides instructions for deploying the Insurance Management System in various environments.

## Prerequisites

### System Requirements
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Docker 20+
- Docker Compose 2+
- Node.js 16+ (for frontend)
- Nginx 1.18+

### Required Tools
- Git
- pip
- virtualenv
- docker
- docker-compose
- npm
- psql

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/insurance-system.git
cd insurance-system
```

### 2. Environment Variables
Create `.env` file in the server directory:
```ini
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/insurance_db
DATABASE_TEST_URL=postgresql://user:password@localhost:5432/insurance_test_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
ELIGIBILITY_SERVICE_URL=https://eligibility.example.com
CLAIMS_SERVICE_URL=https://claims.example.com
AUTH_SERVICE_URL=https://auth.example.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API
API_V1_STR=/api/v1
PROJECT_NAME=Insurance Management System
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### 3. Database Setup
```bash
# Create databases
psql -U postgres -c "CREATE DATABASE insurance_db;"
psql -U postgres -c "CREATE DATABASE insurance_test_db;"

# Run migrations
cd server
alembic upgrade head
```

## Local Development Setup

### 1. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev
```

## Docker Deployment

### 1. Build Images
```bash
# Build backend
docker build -t insurance-backend:latest -f docker/backend/Dockerfile .

# Build frontend
docker build -t insurance-frontend:latest -f docker/frontend/Dockerfile .
```

### 2. Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  db:
    image: postgres:12
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=insurance_db
    ports:
      - "5432:5432"

  redis:
    image: redis:6
    ports:
      - "6379:6379"

  backend:
    image: insurance-backend:latest
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/insurance_db
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "8000:8000"

  frontend:
    image: insurance-frontend:latest
    ports:
      - "3000:3000"
    depends_on:
      - backend

  nginx:
    image: nginx:1.19
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
```

### 3. Run with Docker Compose
```bash
docker-compose up -d
```

## Production Deployment

### 1. Infrastructure Requirements
- Kubernetes cluster
- Container registry
- Load balancer
- SSL certificates
- Monitoring system
- Backup system

### 2. Kubernetes Deployment
Apply Kubernetes manifests:
```bash
# Create namespace
kubectl create namespace insurance-system

# Apply configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy database
kubectl apply -f k8s/database/

# Deploy Redis
kubectl apply -f k8s/redis/

# Deploy backend
kubectl apply -f k8s/backend/

# Deploy frontend
kubectl apply -f k8s/frontend/

# Deploy ingress
kubectl apply -f k8s/ingress/
```

### 3. Database Migration
```bash
# Run migrations
kubectl apply -f k8s/jobs/migrate-database.yaml
```

## Monitoring Setup

### 1. Prometheus
Deploy Prometheus for metrics:
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

### 2. Grafana
Configure Grafana dashboards:
```bash
kubectl apply -f monitoring/grafana-dashboards/
```

### 3. Logging
Setup logging with ELK Stack:
```bash
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch
helm install kibana elastic/kibana
helm install filebeat elastic/filebeat
```

## Backup Strategy

### 1. Database Backups
```bash
# Create backup job
kubectl apply -f k8s/jobs/backup-database.yaml

# Schedule backup cronjob
kubectl apply -f k8s/cronjobs/backup-database.yaml
```

### 2. Application Data
```bash
# Backup persistent volumes
kubectl apply -f k8s/jobs/backup-volumes.yaml
```

## Security Measures

### 1. SSL/TLS Configuration
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.8.0/cert-manager.yaml

# Configure certificates
kubectl apply -f k8s/certificates/
```

### 2. Network Policies
```bash
# Apply network policies
kubectl apply -f k8s/network-policies/
```

## Scaling

### 1. Horizontal Pod Autoscaling
```bash
# Configure HPA
kubectl apply -f k8s/hpa/backend-hpa.yaml
kubectl apply -f k8s/hpa/frontend-hpa.yaml
```

### 2. Vertical Pod Autoscaling
```bash
# Configure VPA
kubectl apply -f k8s/vpa/
```

## Troubleshooting

### Common Issues
1. Database Connection Issues
```bash
# Check database connectivity
kubectl exec -it <pod-name> -- psql -U postgres -d insurance_db
```

2. Redis Connection Issues
```bash
# Check Redis connectivity
kubectl exec -it <pod-name> -- redis-cli ping
```

3. Log Access
```bash
# View backend logs
kubectl logs -f deployment/backend

# View frontend logs
kubectl logs -f deployment/frontend
```

### Health Checks
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost:3000/health
```

## Maintenance

### 1. Database Maintenance
```bash
# Run vacuum
kubectl exec -it <postgres-pod> -- psql -U postgres -d insurance_db -c "VACUUM ANALYZE;"
```

### 2. Cache Maintenance
```bash
# Clear Redis cache
kubectl exec -it <redis-pod> -- redis-cli FLUSHALL
```

### 3. Log Rotation
```bash
# Configure log rotation
kubectl apply -f k8s/config/log-rotation.yaml
```

## Rollback Procedures

### 1. Application Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/backend
kubectl rollout undo deployment/frontend
```

### 2. Database Rollback
```bash
# Rollback migration
alembic downgrade -1
```

## Support

### Contact Information
- Technical Support: tech-support@example.com
- Operations Team: ops@example.com
- Security Team: security@example.com

### Documentation
- API Documentation: https://docs.example.com/api
- Service Documentation: https://docs.example.com/services
- Database Documentation: https://docs.example.com/database
