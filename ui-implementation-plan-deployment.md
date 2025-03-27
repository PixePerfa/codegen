# Deployment Plan

## Overview

This document outlines the deployment plan for the Codegen UI, covering both development and production environments. The plan focuses on creating a seamless deployment process that ensures consistency across environments and enables easy updates and rollbacks.

## Deployment Environments

The Codegen UI will be deployed in three main environments:

1. **Development Environment**: For local development and testing
2. **Staging Environment**: For pre-production testing and validation
3. **Production Environment**: For end-user access

## Deployment Architecture

The deployment architecture defines how the different components of the Codegen UI are deployed and interact with each other:

```
+---------------------------------------------------------------------+
|                        Deployment Architecture                       |
+---------------------------------------------------------------------+
|                                                                     |
|  +-------------------+     +-------------------+     +-----------+   |
|  |   Frontend        |     |   Backend API     |     |  Database |   |
|  | (Nginx/React)     | --> | (FastAPI/Uvicorn) | --> | (Postgres)|   |
|  +-------------------+     +-------------------+     +-----------+   |
|                                    |                                 |
|                                    v                                 |
|                            +-------------------+                     |
|                            |   Task Queue      |                     |
|                            | (Celery/Redis)    |                     |
|                            +-------------------+                     |
|                                                                     |
+---------------------------------------------------------------------+
```

## Development Environment

The development environment is designed for local development and testing, with hot reloading and debugging capabilities.

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm start
```

### Backend Development

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Docker Compose for Development

For a complete development environment with all components, Docker Compose can be used:

```yaml
# docker-compose.dev.yml
version: '3'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_BASE_URL=http://localhost:8000
      - REACT_APP_WS_BASE_URL=ws://localhost:8000/ws
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/codegen_dev
      - SECRET_KEY=dev_secret_key
      - ALLOW_ORIGINS=http://localhost:3000
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=codegen_dev
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data

  redis:
    image: redis:6
    ports:
      - "6379:6379"

volumes:
  postgres_data_dev:
```

## Production Environment

The production environment is designed for end-user access, with optimized performance, security, and reliability.

### Frontend Production Build

```dockerfile
# frontend/Dockerfile
FROM node:14-alpine as build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Backend Production Build

```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose for Production

For a complete production environment with all components, Docker Compose can be used:

```yaml
# docker-compose.prod.yml
version: '3'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    environment:
      - REACT_APP_API_BASE_URL=https://api.codegen.example.com
      - REACT_APP_WS_BASE_URL=wss://api.codegen.example.com/ws
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/codegen_prod
      - SECRET_KEY=${SECRET_KEY}
      - ALLOW_ORIGINS=https://codegen.example.com
      - REDIS_URL=redis://redis:6379/0
    restart: always
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=codegen_prod
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:6
    volumes:
      - redis_data_prod:/data
    restart: always

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/codegen_prod
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379/0
    restart: always
    depends_on:
      - db
      - redis

volumes:
  postgres_data_prod:
  redis_data_prod:
```

## Kubernetes Deployment

For more advanced deployment scenarios, Kubernetes can be used for orchestration:

### Frontend Deployment

```yaml
# kubernetes/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codegen-frontend
  labels:
    app: codegen
    component: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codegen
      component: frontend
  template:
    metadata:
      labels:
        app: codegen
        component: frontend
    spec:
      containers:
      - name: frontend
        image: codegen/frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: REACT_APP_API_BASE_URL
          value: https://api.codegen.example.com
        - name: REACT_APP_WS_BASE_URL
          value: wss://api.codegen.example.com/ws
        resources:
          limits:
            cpu: "0.5"
            memory: "512Mi"
          requests:
            cpu: "0.2"
            memory: "256Mi"
```

### Backend Deployment

```yaml
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codegen-backend
  labels:
    app: codegen
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codegen
      component: backend
  template:
    metadata:
      labels:
        app: codegen
        component: backend
    spec:
      containers:
      - name: backend
        image: codegen/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: codegen-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: codegen-secrets
              key: secret-key
        - name: ALLOW_ORIGINS
          value: https://codegen.example.com
        - name: REDIS_URL
          value: redis://codegen-redis:6379/0
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
          requests:
            cpu: "0.5"
            memory: "512Mi"
```

## Continuous Integration and Deployment (CI/CD)

The CI/CD pipeline will automate the testing, building, and deployment of the Codegen UI:

### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install backend dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest
    
    - name: Run backend tests
      run: |
        cd backend
        pytest
    
    - name: Set up Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '14'
    
    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run frontend tests
      run: |
        cd frontend
        npm test
  
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v1
    
    - name: Login to DockerHub
      uses: docker/login-action@v1
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    
    - name: Build and push frontend
      uses: docker/build-push-action@v2
      with:
        context: ./frontend
        push: true
        tags: codegen/frontend:latest
    
    - name: Build and push backend
      uses: docker/build-push-action@v2
      with:
        context: ./backend
        push: true
        tags: codegen/backend:latest
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v1
    
    - name: Set Kubernetes context
      uses: azure/k8s-set-context@v1
      with:
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f kubernetes/frontend-deployment.yaml
        kubectl apply -f kubernetes/backend-deployment.yaml
        kubectl apply -f kubernetes/database-deployment.yaml
        kubectl apply -f kubernetes/redis-deployment.yaml
        kubectl apply -f kubernetes/celery-deployment.yaml
```

## Desktop Application Deployment

For desktop deployment, Electron will be used to package the application:

### Electron Configuration

```javascript
// electron/main.js
const { app, BrowserWindow } = require('electron');
const path = require('path');
const url = require('url');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  const startUrl = process.env.ELECTRON_START_URL || url.format({
    pathname: path.join(__dirname, '../build/index.html'),
    protocol: 'file:',
    slashes: true,
  });

  mainWindow.loadURL(startUrl);

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

app.on('ready', createWindow);

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', function () {
  if (mainWindow === null) {
    createWindow();
  }
});
```

### Electron Build Configuration

```json
// package.json (frontend)
{
  "name": "codegen-ui",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^17.0.2",
    "react-dom": "^17.0.2",
    "electron": "^13.1.7",
    "electron-builder": "^22.11.7"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "electron-dev": "concurrently \"BROWSER=none npm start\" \"wait-on http://localhost:3000 && electron .\"",
    "electron-pack": "electron-builder -c.extraMetadata.main=build/electron.js",
    "preelectron-pack": "npm run build"
  },
  "build": {
    "appId": "com.codegen.ui",
    "files": [
      "build/**/*",
      "node_modules/**/*"
    ],
    "directories": {
      "buildResources": "assets"
    },
    "mac": {
      "category": "public.app-category.developer-tools"
    },
    "win": {
      "target": "nsis"
    },
    "linux": {
      "target": "deb"
    }
  }
}
```

## Monitoring and Logging

To ensure the health and performance of the deployed application, monitoring and logging will be implemented:

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'codegen-backend'
    scrape_interval: 5s
    static_configs:
      - targets: ['backend:8000']

  - job_name: 'codegen-frontend'
    scrape_interval: 5s
    static_configs:
      - targets: ['frontend:80']
```

### Grafana Dashboard

A Grafana dashboard will be created to visualize metrics from Prometheus, including:

- Request rate and latency
- Error rate
- CPU and memory usage
- Database connection pool status
- Task queue length and processing time

### Logging Configuration

```python
# backend/app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, 'request_id'):
            log_record["request_id"] = record.request_id
            
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logging():
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    logger.addHandler(handler)
    
    return logger
```

## Backup and Disaster Recovery

To ensure data safety and service continuity, backup and disaster recovery procedures will be implemented:

### Database Backup

```bash
#!/bin/bash
# backup.sh

# Set variables
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="codegen-db"
DB_NAME="codegen_prod"
DB_USER="postgres"

# Create backup
docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/codegen_$TIMESTAMP.sql.gz

# Rotate backups (keep last 7 daily, 4 weekly, 3 monthly)
find $BACKUP_DIR -name "codegen_*.sql.gz" -type f -mtime +90 -delete
```

### Disaster Recovery Plan

1. **Database Failure**:
   - Switch to standby database
   - Restore from latest backup if standby is not available
   - Verify data integrity

2. **Application Failure**:
   - Roll back to last known good deployment
   - Restart services
   - Verify functionality

3. **Infrastructure Failure**:
   - Switch to backup region/zone
   - Restore services from backup
   - Verify functionality

## Security Considerations

To ensure the security of the deployed application, the following measures will be implemented:

### HTTPS Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name codegen.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name codegen.example.com;

    ssl_certificate /etc/nginx/ssl/codegen.crt;
    ssl_certificate_key /etc/nginx/ssl/codegen.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Security Headers

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# HTTPS redirect in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOW_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=os.getenv("ENVIRONMENT") == "production",
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'"
    return response
```

## Next Steps

1. Set up development environment with Docker Compose
2. Implement CI/CD pipeline with GitHub Actions
3. Configure monitoring and logging
4. Set up backup and disaster recovery procedures
5. Implement security measures
6. Create deployment documentation for users and administrators