# Integration Plan

## Overview

This document outlines the integration plan for connecting the frontend UI, backend API, and Codegen SDK components of the Codegen UI. The integration focuses on ensuring seamless communication between components while maintaining separation of concerns and enabling efficient data flow.

## Integration Architecture

The integration architecture defines how the different components of the Codegen UI communicate with each other:

```
+---------------------------------------------------------------------+
|                        Integration Architecture                      |
+---------------------------------------------------------------------+
|                                                                     |
|  +-------------------+                      +-------------------+    |
|  |   Frontend UI     |  <---------------->  |   Backend API     |    |
|  | (React/TypeScript)|      REST API        | (Python/FastAPI)  |    |
|  +-------------------+      WebSockets      +-------------------+    |
|                                                      |              |
|                                                      |              |
|                                                      v              |
|                                             +-------------------+    |
|                                             |   Codegen SDK     |    |
|                                             | (Python)          |    |
|                                             +-------------------+    |
|                                                                     |
+---------------------------------------------------------------------+
```

## Key Integration Points

### 1. Frontend to Backend Integration

The frontend UI will communicate with the backend API through:

1. **REST API Calls**: For CRUD operations and data retrieval
2. **WebSocket Connections**: For real-time updates and long-running operations

#### 1.1 REST API Integration

The frontend will use a consistent API client to communicate with the backend:

```typescript
// api/client.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { store } from '../state/store';
import { refreshToken, logout } from '../state/slices/authSlice';

export class ApiClient {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        const state = store.getState();
        const token = state.auth.token;
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // Handle token expiration
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            // Try to refresh the token
            await store.dispatch(refreshToken());
            const state = store.getState();
            const newToken = state.auth.token;
            
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // If refresh fails, logout
            store.dispatch(logout());
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Generic request method
  async request<T>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.client(config);
    return response.data;
  }

  // Convenience methods
  async get<T>(url: string, params?: any): Promise<T> {
    return this.request<T>({ method: 'GET', url, params });
  }

  async post<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'POST', url, data });
  }

  async put<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'PUT', url, data });
  }

  async delete<T>(url: string): Promise<T> {
    return this.request<T>({ method: 'DELETE', url });
  }
}

// Create and export a singleton instance
export const apiClient = new ApiClient(process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000');
```

#### 1.2 WebSocket Integration

The frontend will use a WebSocket client for real-time communication:

```typescript
// api/websocket.ts
import { store } from '../state/store';
import { addNotification } from '../state/slices/notificationSlice';
import { updateOperationProgress } from '../state/slices/operationSlice';

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private baseUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout = 1000;
  private messageHandlers: Map<string, (data: any) => void> = new Map();

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return;
    }

    const state = store.getState();
    const token = state.auth.token;
    
    this.socket = new WebSocket(`${this.baseUrl}?token=${token}`);
    
    this.socket.onopen = this.handleOpen.bind(this);
    this.socket.onmessage = this.handleMessage.bind(this);
    this.socket.onclose = this.handleClose.bind(this);
    this.socket.onerror = this.handleError.bind(this);
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  send(message: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  registerHandler(messageType: string, handler: (data: any) => void) {
    this.messageHandlers.set(messageType, handler);
  }

  unregisterHandler(messageType: string) {
    this.messageHandlers.delete(messageType);
  }

  private handleOpen(event: Event) {
    console.log('WebSocket connected');
    this.reconnectAttempts = 0;
  }

  private handleMessage(event: MessageEvent) {
    try {
      const message = JSON.parse(event.data);
      const messageType = message.type;
      
      // Handle standard message types
      if (messageType === 'operation_progress') {
        store.dispatch(updateOperationProgress(message));
      } else if (messageType === 'notification') {
        store.dispatch(addNotification(message));
      }
      
      // Call registered handler for this message type
      const handler = this.messageHandlers.get(messageType);
      if (handler) {
        handler(message);
      }
    } catch (error) {
      console.error('Error handling WebSocket message', error);
    }
  }

  private handleClose(event: CloseEvent) {
    console.log('WebSocket disconnected', event.code, event.reason);
    
    // Attempt to reconnect if not a normal closure
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), this.reconnectTimeout * this.reconnectAttempts);
    }
  }

  private handleError(event: Event) {
    console.error('WebSocket error', event);
  }
}

// Create and export a singleton instance
export const wsClient = new WebSocketClient(
  process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000/ws'
);
```

### 2. Backend to Codegen SDK Integration

The backend API will integrate with the Codegen SDK through:

1. **Direct SDK Calls**: For immediate operations
2. **Background Tasks**: For long-running operations

#### 2.1 Direct SDK Integration

The backend will use a service layer to interact with the Codegen SDK:

```python
# services/codegen/analysis.py
from typing import Dict, Any, List, Optional
import os

from ....codegen.sdk.codebase import Codebase
from .codebase import get_codebase

def analyze_dependencies(project_id: int) -> Dict[str, Any]:
    """Analyze dependencies in a project."""
    codebase = get_codebase(project_id)
    
    # Use Codegen SDK to analyze dependencies
    dependencies = codebase.analyze_dependencies()
    
    # Format the result for API response
    result = {
        "modules": [],
        "dependencies": []
    }
    
    for module in dependencies.modules:
        result["modules"].append({
            "id": module.id,
            "name": module.name,
            "path": module.path,
            "type": module.type
        })
    
    for dep in dependencies.dependencies:
        result["dependencies"].append({
            "source": dep.source,
            "target": dep.target,
            "type": dep.type
        })
    
    return result

def analyze_symbols(project_id: int, file_path: Optional[str] = None) -> Dict[str, Any]:
    """Analyze symbols in a project or file."""
    codebase = get_codebase(project_id)
    
    # Use Codegen SDK to analyze symbols
    if file_path:
        symbols = codebase.analyze_symbols(file_path)
    else:
        symbols = codebase.analyze_all_symbols()
    
    # Format the result for API response
    result = {
        "symbols": []
    }
    
    for symbol in symbols:
        result["symbols"].append({
            "id": symbol.id,
            "name": symbol.name,
            "type": symbol.type,
            "file_path": symbol.file_path,
            "line": symbol.line,
            "column": symbol.column,
            "end_line": symbol.end_line,
            "end_column": symbol.end_column,
            "parent": symbol.parent,
            "children": symbol.children
        })
    
    return result

def analyze_complexity(project_id: int, file_path: Optional[str] = None) -> Dict[str, Any]:
    """Analyze code complexity in a project or file."""
    codebase = get_codebase(project_id)
    
    # Use Codegen SDK to analyze complexity
    if file_path:
        complexity = codebase.analyze_complexity(file_path)
    else:
        complexity = codebase.analyze_all_complexity()
    
    # Format the result for API response
    result = {
        "files": []
    }
    
    for file_result in complexity:
        file_data = {
            "path": file_result.path,
            "total_complexity": file_result.total_complexity,
            "functions": []
        }
        
        for func in file_result.functions:
            file_data["functions"].append({
                "name": func.name,
                "complexity": func.complexity,
                "line": func.line,
                "end_line": func.end_line
            })
        
        result["files"].append(file_data)
    
    return result
```

#### 2.2 Background Task Integration

The backend will use a task queue for long-running operations:

```python
# services/tasks/jobs.py
from celery import shared_task
from typing import Dict, Any, Optional
import time
import json

from ...db.crud import get_project, update_operation_status
from ...services.codegen.codebase import get_codebase, close_codebase
from ...services.codegen.operations import execute_operation_impl
from ...core.websocket import broadcast_to_user

@shared_task
def run_operation(
    project_id: int,
    operation: str,
    params: Dict[str, Any],
    user_id: int,
    operation_id: str
):
    """Run a Codegen operation as a background task."""
    try:
        # Update operation status to running
        update_operation_status(operation_id, "running", progress=0)
        
        # Send progress update
        broadcast_to_user(user_id, {
            "type": "operation_progress",
            "operation_id": operation_id,
            "operation": operation,
            "progress": 0,
            "status": "running"
        })
        
        # Get the project and codebase
        project = get_project(project_id)
        codebase = get_codebase(project_id)
        
        # Execute the operation
        result = execute_operation_impl(codebase, operation, params)
        
        # Update operation status to completed
        update_operation_status(
            operation_id,
            "completed",
            progress=100,
            result=json.dumps(result)
        )
        
        # Send completion update
        broadcast_to_user(user_id, {
            "type": "operation_progress",
            "operation_id": operation_id,
            "operation": operation,
            "progress": 100,
            "status": "completed",
            "result": result
        })
        
        return result
    except Exception as e:
        # Update operation status to failed
        update_operation_status(
            operation_id,
            "failed",
            error=str(e)
        )
        
        # Send error update
        broadcast_to_user(user_id, {
            "type": "operation_progress",
            "operation_id": operation_id,
            "operation": operation,
            "status": "failed",
            "error": str(e)
        })
        
        # Re-raise the exception for Celery to handle
        raise
```

### 3. Data Format Standardization

To ensure consistent data exchange between components, the integration will define standard data formats for:

1. **Project Data**: Structure of project metadata
2. **File Data**: Structure of file content and metadata
3. **Symbol Data**: Structure of code symbols
4. **Analysis Results**: Structure of analysis results
5. **Operation Requests**: Structure of operation requests
6. **Operation Results**: Structure of operation results

#### 3.1 TypeScript Type Definitions

```typescript
// types/api.ts

// Project types
export interface Project {
  id: number;
  name: string;
  description?: string;
  root_path: string;
  created_at: string;
  updated_at: string;
}

// File types
export interface ProjectFile {
  id: number;
  path: string;
  content: string;
  project_id: number;
  created_at: string;
  updated_at: string;
}

// Symbol types
export interface CodeSymbol {
  id: string;
  name: string;
  type: string;
  file_path: string;
  line: number;
  column: number;
  end_line: number;
  end_column: number;
  parent?: string;
  children: string[];
}

// Analysis result types
export interface DependencyAnalysisResult {
  modules: {
    id: string;
    name: string;
    path: string;
    type: string;
  }[];
  dependencies: {
    source: string;
    target: string;
    type: string;
  }[];
}

export interface SymbolAnalysisResult {
  symbols: CodeSymbol[];
}

export interface ComplexityAnalysisResult {
  files: {
    path: string;
    total_complexity: number;
    functions: {
      name: string;
      complexity: number;
      line: number;
      end_line: number;
    }[];
  }[];
}

// Operation types
export interface OperationRequest {
  operation: string;
  params: Record<string, any>;
}

export interface OperationResult {
  operation_id: string;
  operation: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  result?: any;
  error?: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface OperationProgressMessage extends WebSocketMessage {
  type: 'operation_progress';
  operation_id: string;
  operation: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  result?: any;
  error?: string;
}

export interface NotificationMessage extends WebSocketMessage {
  type: 'notification';
  message: string;
  level: 'info' | 'success' | 'warning' | 'error';
}
```

#### 3.2 Python Data Models

```python
# api/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

# Project models
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    root_path: str

class Project(ProjectCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# File models
class ProjectFileCreate(BaseModel):
    path: str
    content: str

class ProjectFile(ProjectFileCreate):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Symbol models
class CodeSymbol(BaseModel):
    id: str
    name: str
    type: str
    file_path: str
    line: int
    column: int
    end_line: int
    end_column: int
    parent: Optional[str] = None
    children: List[str] = []

# Analysis result models
class Module(BaseModel):
    id: str
    name: str
    path: str
    type: str

class Dependency(BaseModel):
    source: str
    target: str
    type: str

class DependencyAnalysisResult(BaseModel):
    modules: List[Module]
    dependencies: List[Dependency]

class SymbolAnalysisResult(BaseModel):
    symbols: List[CodeSymbol]

class FunctionComplexity(BaseModel):
    name: str
    complexity: int
    line: int
    end_line: int

class FileComplexity(BaseModel):
    path: str
    total_complexity: int
    functions: List[FunctionComplexity]

class ComplexityAnalysisResult(BaseModel):
    files: List[FileComplexity]

# Operation models
class OperationRequest(BaseModel):
    operation: str
    params: Dict[str, Any] = {}

class OperationResult(BaseModel):
    operation_id: str
    operation: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# WebSocket message models
class WebSocketMessage(BaseModel):
    type: str

class OperationProgressMessage(WebSocketMessage):
    type: str = "operation_progress"
    operation_id: str
    operation: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class NotificationMessage(WebSocketMessage):
    type: str = "notification"
    message: str
    level: str
```

## Integration Testing

The integration between components will be tested using:

1. **API Integration Tests**: Testing the communication between frontend and backend
2. **SDK Integration Tests**: Testing the communication between backend and SDK
3. **End-to-End Tests**: Testing the complete flow from UI to SDK and back

### API Integration Tests

```typescript
// tests/api-integration.test.ts
import { apiClient } from '../src/api/client';
import { Project, ProjectFile } from '../src/types/api';

describe('API Integration Tests', () => {
  let testProject: Project;
  let testFile: ProjectFile;

  beforeAll(async () => {
    // Set up test data
    testProject = await apiClient.post<Project>('/projects', {
      name: 'Test Project',
      description: 'Project for integration tests',
      root_path: '/test'
    });
  });

  afterAll(async () => {
    // Clean up test data
    await apiClient.delete(`/projects/${testProject.id}`);
  });

  test('should create a file in the project', async () => {
    testFile = await apiClient.post<ProjectFile>(`/projects/${testProject.id}/files`, {
      path: 'test.py',
      content: 'print("Hello, world!")'
    });

    expect(testFile).toBeDefined();
    expect(testFile.path).toBe('test.py');
    expect(testFile.content).toBe('print("Hello, world!")');
  });

  test('should get file content', async () => {
    const file = await apiClient.get<ProjectFile>(`/projects/${testProject.id}/files/${testFile.id}`);

    expect(file).toBeDefined();
    expect(file.content).toBe('print("Hello, world!")');
  });

  test('should update file content', async () => {
    const updatedFile = await apiClient.put<ProjectFile>(`/projects/${testProject.id}/files/${testFile.id}`, {
      content: 'print("Updated content")'
    });

    expect(updatedFile).toBeDefined();
    expect(updatedFile.content).toBe('print("Updated content")');
  });

  test('should analyze file symbols', async () => {
    const result = await apiClient.get(`/projects/${testProject.id}/analysis/symbols`, {
      file_path: 'test.py'
    });

    expect(result).toBeDefined();
    expect(result.symbols).toBeDefined();
    // Check for specific symbols based on the file content
  });
});
```

### SDK Integration Tests

```python
# tests/test_sdk_integration.py
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.codegen.codebase import get_codebase, create_codebase
from app.db.crud import create_project, create_file

client = TestClient(app)

@pytest.fixture
def test_project():
    # Create a test project
    project = create_project({
        "name": "Test Project",
        "description": "Project for SDK integration tests",
        "root_path": "/test"
    }, user_id=1)
    
    # Create a test file
    file = create_file(project.id, {
        "path": "test.py",
        "content": "def hello():\n    print('Hello, world!')\n\nhello()"
    })
    
    return project

def test_codebase_creation(test_project):
    # Test that a codebase can be created for the project
    codebase = create_codebase(test_project.id)
    
    assert codebase is not None
    assert codebase.root_dir is not None

def test_file_parsing(test_project):
    # Test that files can be parsed
    codebase = get_codebase(test_project.id)
    
    # Parse the codebase
    codebase.parse()
    
    # Check that the file was parsed
    assert "test.py" in codebase.files

def test_symbol_analysis(test_project):
    # Test symbol analysis
    codebase = get_codebase(test_project.id)
    
    # Analyze symbols
    symbols = codebase.analyze_symbols("test.py")
    
    # Check that the function was found
    assert any(s.name == "hello" for s in symbols)

def test_operation_execution(test_project):
    # Test operation execution
    from app.services.codegen.operations import execute_operation_impl
    
    codebase = get_codebase(test_project.id)
    
    # Execute a search operation
    result = execute_operation_impl(codebase, "search_symbols", {
        "query": "hello"
    })
    
    # Check that the function was found
    assert result is not None
    assert "symbols" in result
    assert any(s["name"] == "hello" for s in result["symbols"])
```

## Deployment Integration

The deployment integration will ensure that all components are deployed together and can communicate with each other:

1. **Development Environment**: Local development setup with hot reloading
2. **Production Environment**: Containerized deployment with proper security

### Development Environment

For local development, the components will be run separately with appropriate configuration:

```bash
# Start the backend API
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Start the frontend development server
cd frontend
npm start
```

### Production Environment

For production deployment, the components will be containerized using Docker:

```dockerfile
# Backend Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Frontend Dockerfile
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

Docker Compose will be used to run the components together:

```yaml
# docker-compose.yml
version: '3'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/codegen
      - SECRET_KEY=your-secret-key
      - ALLOW_ORIGINS=http://localhost:3000,http://frontend:80
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    environment:
      - REACT_APP_API_BASE_URL=http://localhost:8000
      - REACT_APP_WS_BASE_URL=ws://localhost:8000/ws

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=codegen
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## Next Steps

1. Implement the frontend API client and WebSocket client
2. Implement the backend service layer for Codegen SDK integration
3. Define standard data formats for communication
4. Implement integration tests
5. Set up development and production deployment configurations