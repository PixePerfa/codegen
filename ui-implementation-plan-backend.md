# Backend API Implementation Plan

## Overview

This document outlines the implementation plan for the backend API component of the Codegen UI. The backend API will provide a bridge between the frontend UI and the Codegen SDK, enabling users to interact with codebases through a graphical interface.

## Architecture

The backend API will be implemented as a Python FastAPI application that provides a RESTful API and WebSocket connections for real-time updates. The architecture consists of the following key components:

```
+---------------------------------------------------------------------+
|                        Backend Architecture                          |
+---------------------------------------------------------------------+
|                                                                     |
|  +-------------------+  +-------------------+  +-------------------+ |
|  |   API Endpoints   |  |   Codegen SDK     |  |   Authentication  | |
|  |                   |  |   Integration     |  |                   | |
|  +-------------------+  +-------------------+  +-------------------+ |
|                                                                     |
|  +-------------------+  +-------------------+  +-------------------+ |
|  | WebSocket Server  |  |   Task Queue      |  |   Data Storage    | |
|  |                   |  |                   |  |                   | |
|  +-------------------+  +-------------------+  +-------------------+ |
|                                                                     |
+---------------------------------------------------------------------+
```

### Key Components

#### 1. API Endpoints

The API endpoints will provide a RESTful interface for the frontend to interact with the backend, including:

- **Project Endpoints**: Create, read, update, delete projects
- **File Endpoints**: File operations, content retrieval, saving
- **Analysis Endpoints**: Code analysis, metrics, relationships
- **Transformation Endpoints**: Code transformations, refactoring operations
- **User Endpoints**: User management, authentication, authorization

These endpoints will be implemented using FastAPI's routing system with comprehensive input validation and error handling.

#### 2. Codegen SDK Integration

The Codegen SDK integration will provide a bridge between the API endpoints and the Codegen SDK, including:

- **Codebase Management**: Creating and managing Codegen codebase instances
- **Operation Execution**: Executing Codegen operations and transformations
- **Result Formatting**: Formatting results for API responses
- **Error Handling**: Handling and translating Codegen errors

This integration will ensure that all Codegen capabilities are accessible through the API while maintaining separation of concerns.

#### 3. Authentication and Authorization

The authentication and authorization system will secure the API and ensure that users can only access resources they are authorized to access, including:

- **User Authentication**: JWT-based authentication
- **Role-based Authorization**: Role-based access control
- **API Key Management**: API key generation and validation
- **Session Management**: User session tracking and management

This system will be implemented using FastAPI's security utilities with JWT tokens for authentication.

#### 4. WebSocket Server

The WebSocket server will provide real-time updates to the frontend, including:

- **Operation Progress**: Real-time progress updates for long-running operations
- **Collaborative Editing**: Real-time updates for collaborative editing
- **Notifications**: Real-time notifications for events
- **User Presence**: Real-time updates for user presence

This will be implemented using FastAPI's WebSocket support with a custom protocol for different message types.

#### 5. Task Queue

The task queue will handle long-running operations asynchronously, including:

- **Background Processing**: Running operations in the background
- **Job Management**: Managing and tracking job status
- **Result Storage**: Storing and retrieving operation results
- **Error Handling**: Handling and reporting errors in background tasks

This will be implemented using Celery with Redis as the message broker for reliable task execution.

#### 6. Data Storage

The data storage system will persist application data, including:

- **Project Metadata**: Project configuration, settings, metadata
- **User Data**: User accounts, preferences, history
- **Operation Results**: Results of operations and analyses
- **Collaboration Data**: Shared projects, comments, annotations

This will be implemented using SQLAlchemy with SQLite for local deployment and PostgreSQL for server deployment.

## Implementation Details

### 1. Project Structure

```
/src
  /api
    /endpoints
      /projects.py
      /files.py
      /analysis.py
      /transformations.py
      /users.py
    /websockets
      /handlers.py
      /protocol.py
    /dependencies.py
    /security.py
  /core
    /config.py
    /security.py
    /exceptions.py
  /db
    /models.py
    /crud.py
    /session.py
  /services
    /codegen
      /codebase.py
      /operations.py
      /analysis.py
    /storage
      /local.py
      /remote.py
    /tasks
      /worker.py
      /jobs.py
  /utils
    /formatting.py
    /validation.py
    /helpers.py
  main.py
```

### 2. Core API Endpoints

#### 2.1 Project Endpoints

```python
# projects.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.session import get_db
from ...db.models import Project
from ...db.crud import create_project, get_project, update_project, delete_project
from ...services.codegen.codebase import create_codebase
from ...core.security import get_current_user

router = APIRouter()

@router.post("/projects", response_model=Project)
def create_project_endpoint(
    project_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new project."""
    project = create_project(db, project_data, current_user.id)
    return project

@router.get("/projects", response_model=List[Project])
def get_projects_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all projects for the current user."""
    projects = get_projects(db, current_user.id, skip=skip, limit=limit)
    return projects

@router.get("/projects/{project_id}", response_model=Project)
def get_project_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific project by ID."""
    project = get_project(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/projects/{project_id}", response_model=Project)
def update_project_endpoint(
    project_id: int,
    project_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a project."""
    project = get_project(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    updated_project = update_project(db, project_id, project_data)
    return updated_project

@router.delete("/projects/{project_id}")
def delete_project_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a project."""
    project = get_project(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    delete_project(db, project_id)
    return {"message": "Project deleted successfully"}
```

#### 2.2 File Endpoints

```python
# files.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.session import get_db
from ...db.models import ProjectFile
from ...db.crud import get_project, get_file, create_file, update_file, delete_file
from ...services.codegen.codebase import get_codebase
from ...core.security import get_current_user

router = APIRouter()

@router.get("/projects/{project_id}/files", response_model=List[ProjectFile])
def get_files_endpoint(
    project_id: int,
    path: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all files in a project, optionally filtered by path."""
    project = get_project(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    files = get_files(db, project_id, path=path)
    return files

@router.get("/projects/{project_id}/files/{file_id}", response_model=ProjectFile)
def get_file_endpoint(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific file by ID."""
    project = get_project(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file = get_file(db, file_id)
    if not file or file.project_id != project_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file

@router.post("/projects/{project_id}/files", response_model=ProjectFile)
def create_file_endpoint(
    project_id: int,
    file_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new file in a project."""
    project = get_project(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file = create_file(db, project_id, file_data)
    
    # Update the codebase
    codebase = get_codebase(project_id)
    codebase.add_file(file.path, file.content)
    
    return file

@router.put("/projects/{project_id}/files/{file_id}", response_model=ProjectFile)
def update_file_endpoint(
    project_id: int,
    file_id: int,
    file_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a file in a project."""
    project = get_project(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file = get_file(db, file_id)
    if not file or file.project_id != project_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    updated_file = update_file(db, file_id, file_data)
    
    # Update the codebase
    codebase = get_codebase(project_id)
    codebase.update_file(updated_file.path, updated_file.content)
    
    return updated_file

@router.delete("/projects/{project_id}/files/{file_id}")
def delete_file_endpoint(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a file from a project."""
    project = get_project(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file = get_file(db, file_id)
    if not file or file.project_id != project_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Update the codebase
    codebase = get_codebase(project_id)
    codebase.remove_file(file.path)
    
    delete_file(db, file_id)
    return {"message": "File deleted successfully"}
```

### 3. Codegen SDK Integration

#### 3.1 Codebase Management

```python
# codebase.py
from typing import Dict, Optional
import os
import tempfile
import shutil

from ....codegen.sdk.codebase import Codebase

# Cache of codebase instances
_codebases: Dict[int, Codebase] = {}

def get_codebase(project_id: int) -> Codebase:
    """Get or create a Codebase instance for a project."""
    if project_id in _codebases:
        return _codebases[project_id]
    
    # Create a new codebase
    codebase = create_codebase(project_id)
    _codebases[project_id] = codebase
    return codebase

def create_codebase(project_id: int) -> Codebase:
    """Create a new Codebase instance for a project."""
    # Create a temporary directory for the project
    project_dir = tempfile.mkdtemp(prefix=f"codegen_project_{project_id}_")
    
    # Initialize the codebase
    codebase = Codebase(project_dir)
    
    # Load files from the database
    from ....db.crud import get_files
    from ....db.session import get_db
    
    db = next(get_db())
    files = get_files(db, project_id)
    
    for file in files:
        file_path = os.path.join(project_dir, file.path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w") as f:
            f.write(file.content)
    
    # Parse the codebase
    codebase.parse()
    
    return codebase

def close_codebase(project_id: int):
    """Close a Codebase instance and clean up resources."""
    if project_id in _codebases:
        codebase = _codebases[project_id]
        
        # Clean up temporary directory
        if os.path.exists(codebase.root_dir):
            shutil.rmtree(codebase.root_dir)
        
        del _codebases[project_id]
```

#### 3.2 Operation Execution

```python
# operations.py
from typing import Dict, Any, List, Optional
import asyncio
from fastapi import WebSocket

from ....codegen.sdk.codebase import Codebase
from .codebase import get_codebase

async def execute_operation(
    project_id: int,
    operation: str,
    params: Dict[str, Any],
    websocket: Optional[WebSocket] = None
) -> Dict[str, Any]:
    """Execute a Codegen operation on a project."""
    codebase = get_codebase(project_id)
    
    # Send initial progress update
    if websocket:
        await websocket.send_json({
            "type": "operation_progress",
            "operation": operation,
            "progress": 0,
            "status": "started"
        })
    
    try:
        # Execute the operation
        result = await _execute_operation_impl(codebase, operation, params, websocket)
        
        # Send final progress update
        if websocket:
            await websocket.send_json({
                "type": "operation_progress",
                "operation": operation,
                "progress": 100,
                "status": "completed",
                "result": result
            })
        
        return result
    except Exception as e:
        # Send error update
        if websocket:
            await websocket.send_json({
                "type": "operation_progress",
                "operation": operation,
                "status": "error",
                "error": str(e)
            })
        
        raise

async def _execute_operation_impl(
    codebase: Codebase,
    operation: str,
    params: Dict[str, Any],
    websocket: Optional[WebSocket] = None
) -> Dict[str, Any]:
    """Implementation of operation execution."""
    # Map operation to Codegen SDK method
    operation_map = {
        "search_files": _search_files,
        "search_symbols": _search_symbols,
        "get_file_content": _get_file_content,
        "update_file_content": _update_file_content,
        "rename_symbol": _rename_symbol,
        "move_symbol": _move_symbol,
        "get_symbol_references": _get_symbol_references,
        "get_dependencies": _get_dependencies,
        # Add more operations as needed
    }
    
    if operation not in operation_map:
        raise ValueError(f"Unknown operation: {operation}")
    
    # Execute the operation
    operation_func = operation_map[operation]
    result = await operation_func(codebase, params, websocket)
    
    return result

async def _search_files(
    codebase: Codebase,
    params: Dict[str, Any],
    websocket: Optional[WebSocket] = None
) -> Dict[str, Any]:
    """Search for files in the codebase."""
    query = params.get("query", "")
    file_pattern = params.get("file_pattern", "*")
    
    # Use Codegen SDK to search files
    files = codebase.search_files(query, file_pattern)
    
    return {
        "files": [
            {
                "path": file.path,
                "name": os.path.basename(file.path),
                "size": os.path.getsize(os.path.join(codebase.root_dir, file.path)),
                "type": os.path.splitext(file.path)[1][1:],  # Extension without dot
            }
            for file in files
        ]
    }

# Implement other operation functions similarly
```

### 4. WebSocket Server

```python
# handlers.py
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Any
import json

from ...core.security import get_current_user_ws
from ...services.codegen.operations import execute_operation

# Active WebSocket connections
active_connections: Dict[int, List[WebSocket]] = {}

async def connect(websocket: WebSocket, user = Depends(get_current_user_ws)):
    """Handle WebSocket connection."""
    await websocket.accept()
    
    if user.id not in active_connections:
        active_connections[user.id] = []
    
    active_connections[user.id].append(websocket)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle message
            await handle_message(websocket, message, user)
    except WebSocketDisconnect:
        # Remove connection on disconnect
        active_connections[user.id].remove(websocket)
        if not active_connections[user.id]:
            del active_connections[user.id]

async def handle_message(websocket: WebSocket, message: Dict[str, Any], user: Any):
    """Handle WebSocket message."""
    message_type = message.get("type")
    
    if message_type == "operation":
        # Execute operation
        project_id = message.get("project_id")
        operation = message.get("operation")
        params = message.get("params", {})
        
        await execute_operation(project_id, operation, params, websocket)
    elif message_type == "ping":
        # Respond to ping
        await websocket.send_json({"type": "pong"})
    else:
        # Unknown message type
        await websocket.send_json({
            "type": "error",
            "error": f"Unknown message type: {message_type}"
        })

async def broadcast_to_user(user_id: int, message: Dict[str, Any]):
    """Broadcast a message to all connections for a user."""
    if user_id in active_connections:
        for connection in active_connections[user_id]:
            await connection.send_json(message)
```

### 5. Database Models

```python
# models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    root_path = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    owner = relationship("User", back_populates="projects")
    files = relationship("ProjectFile", back_populates="project")

class ProjectFile(Base):
    __tablename__ = "project_files"
    
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, index=True)
    content = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    project = relationship("Project", back_populates="files")
```

## Integration with Frontend

The backend API will integrate with the frontend through a combination of REST API calls and WebSocket connections. The integration will focus on:

1. **API Endpoints**: RESTful API endpoints for CRUD operations
2. **WebSocket Communication**: Real-time updates and long-running operations
3. **Authentication**: Secure authentication using JWT tokens
4. **Error Handling**: Comprehensive error handling and reporting
5. **Performance**: Optimized data transfer and processing

## Testing Strategy

The backend API will be tested using a combination of:

1. **Unit Tests**: Testing individual components and functions
2. **Integration Tests**: Testing API endpoints and WebSocket handlers
3. **End-to-End Tests**: Testing complete workflows
4. **Load Tests**: Testing performance under load

## Deployment

The backend API will be deployed as:

1. **Docker Container**: Containerized deployment for easy scaling
2. **Development Server**: Local development server with hot reloading
3. **Production Server**: Production-ready server with proper security

## Next Steps

1. Set up project structure and dependencies
2. Implement core API endpoints
3. Integrate with Codegen SDK
4. Implement WebSocket server
5. Set up database models and migrations
6. Implement authentication and authorization
7. Add comprehensive testing
8. Set up deployment configuration