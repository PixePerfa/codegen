from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import asyncio
from uuid import uuid4

from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.file import File as CodegenFile
from codegen.sdk.core.analysis import analyze_complexity, analyze_dependencies

app = FastAPI(title="Codegen UI API", description="API for the Codegen UI")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, in production this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active codebases
active_codebases = {}
active_connections = {}

# Models
class ProjectRequest(BaseModel):
    path: str
    language: Optional[str] = None

class FileRequest(BaseModel):
    path: str

class FileContentRequest(BaseModel):
    path: str
    content: str

class SymbolRequest(BaseModel):
    name: str

class SearchRequest(BaseModel):
    query: str
    file_pattern: Optional[str] = None

class TransformRequest(BaseModel):
    operation: str
    params: Dict[str, Any]

class BatchOperationRequest(BaseModel):
    operation: str
    files: List[str]
    params: Dict[str, Any]

class AnalysisRequest(BaseModel):
    type: str
    target: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class GitOperationRequest(BaseModel):
    operation: str
    params: Dict[str, Any]

# Dependency to get active codebase
def get_codebase(project_id: str):
    if project_id not in active_codebases:
        raise HTTPException(status_code=404, detail="Project not found")
    return active_codebases[project_id]

# Routes
@app.post("/projects", status_code=201)
async def create_project(request: ProjectRequest):
    project_id = str(uuid4())
    
    try:
        language_enum = None
        if request.language:
            language_enum = ProgrammingLanguage[request.language.upper()]
        
        codebase = Codebase(request.path, language=language_enum)
        active_codebases[project_id] = codebase
        
        return {
            "id": project_id,
            "name": codebase.name,
            "language": codebase.language.name,
            "path": request.path
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects")
async def list_projects():
    result = []
    for project_id, codebase in active_codebases.items():
        result.append({
            "id": project_id,
            "name": codebase.name,
            "language": codebase.language.name,
            "path": str(codebase.repo_path)
        })
    return result

@app.get("/projects/{project_id}")
async def get_project(project_id: str, codebase: Codebase = Depends(get_codebase)):
    return {
        "id": project_id,
        "name": codebase.name,
        "language": codebase.language.name,
        "path": str(codebase.repo_path)
    }

@app.get("/projects/{project_id}/files")
async def list_files(project_id: str, codebase: Codebase = Depends(get_codebase)):
    files = codebase.files(extensions="*")
    return [{"path": file.path, "is_source": hasattr(file, "symbols")} for file in files]

@app.get("/projects/{project_id}/files/{path:path}")
async def get_file(path: str, project_id: str, codebase: Codebase = Depends(get_codebase)):
    try:
        file = codebase.get_file(path)
        return {
            "path": file.path,
            "content": file.content,
            "is_source": hasattr(file, "symbols"),
            "symbols": [{"name": s.name, "type": s.symbol_type.name} for s in getattr(file, "symbols", [])]
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/projects/{project_id}/files")
async def create_file(
    project_id: str, 
    request: FileContentRequest, 
    codebase: Codebase = Depends(get_codebase)
):
    try:
        file = codebase.create_file(request.path, request.content)
        return {
            "path": file.path,
            "content": file.content,
            "is_source": hasattr(file, "symbols")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/projects/{project_id}/files/{path:path}")
async def update_file(
    path: str,
    project_id: str, 
    request: FileContentRequest, 
    codebase: Codebase = Depends(get_codebase)
):
    try:
        file = codebase.get_file(path)
        file.content = request.content
        codebase.commit()
        return {
            "path": file.path,
            "content": file.content,
            "is_source": hasattr(file, "symbols")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/projects/{project_id}/files/{path:path}")
async def delete_file(
    path: str,
    project_id: str, 
    codebase: Codebase = Depends(get_codebase)
):
    try:
        # Check if file exists
        file = codebase.get_file(path)
        
        # Delete the file from the filesystem
        os.remove(os.path.join(codebase.repo_path, path))
        
        # Commit the changes to the codebase
        codebase.commit()
        
        return {"message": f"File {path} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_id}/symbols")
async def list_symbols(project_id: str, codebase: Codebase = Depends(get_codebase)):
    symbols = codebase.symbols
    return [
        {
            "name": symbol.name,
            "type": symbol.symbol_type.name,
            "file_path": symbol.file.path,
            "line": symbol.line,
            "column": symbol.column
        }
        for symbol in symbols
    ]

@app.get("/projects/{project_id}/classes")
async def list_classes(project_id: str, codebase: Codebase = Depends(get_codebase)):
    classes = codebase.classes
    return [
        {
            "name": cls.name,
            "file_path": cls.file.path,
            "line": cls.line,
            "column": cls.column,
            "methods": [
                {"name": method.name, "line": method.line, "column": method.column}
                for method in cls.methods
            ]
        }
        for cls in classes
    ]

@app.get("/projects/{project_id}/functions")
async def list_functions(project_id: str, codebase: Codebase = Depends(get_codebase)):
    functions = codebase.functions
    return [
        {
            "name": func.name,
            "file_path": func.file.path,
            "line": func.line,
            "column": func.column,
            "parameters": [param.name for param in func.parameters]
        }
        for func in functions
    ]

@app.post("/projects/{project_id}/search")
async def search_codebase(
    project_id: str, 
    request: SearchRequest, 
    codebase: Codebase = Depends(get_codebase)
):
    try:
        # Use ripgrep to search the codebase
        import subprocess
        
        cmd = ["rg", "--json", request.query]
        if request.file_pattern:
            cmd.extend(["-g", request.file_pattern])
        
        result = subprocess.run(
            cmd, 
            cwd=codebase.repo_path, 
            capture_output=True, 
            text=True
        )
        
        # Parse the JSON output
        matches = []
        for line in result.stdout.splitlines():
            try:
                data = json.loads(line)
                if "data" in data and data.get("type") == "match":
                    match_data = data["data"]
                    matches.append({
                        "path": match_data["path"]["text"],
                        "line_number": match_data["line_number"],
                        "lines": match_data["lines"]["text"],
                        "submatches": [
                            {
                                "match": m["match"]["text"],
                                "start": m["start"],
                                "end": m["end"]
                            }
                            for m in match_data["submatches"]
                        ]
                    })
            except json.JSONDecodeError:
                continue
        
        return {"matches": matches}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/projects/{project_id}/transform")
async def transform_codebase(
    project_id: str, 
    request: TransformRequest, 
    codebase: Codebase = Depends(get_codebase)
):
    try:
        # Map operation to method
        operations = {
            "rename_symbol": lambda params: codebase.get_symbol(params["symbol_name"]).rename(params["new_name"]),
            "move_symbol": lambda params: codebase.get_symbol(params["symbol_name"]).move_to(
                codebase.get_file(params["target_file"])
            ),
            "rename_file": lambda params: codebase.get_file(params["file_path"]).rename(params["new_name"]),
            "commit": lambda params: codebase.commit(),
            "git_commit": lambda params: codebase.git_commit(params["message"])
        }
        
        if request.operation not in operations:
            raise ValueError(f"Unknown operation: {request.operation}")
        
        # Execute the operation
        result = operations[request.operation](request.params)
        
        # Commit changes if not already committed
        if request.operation != "commit" and request.operation != "git_commit":
            codebase.commit()
        
        return {"status": "success", "result": str(result)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/projects/{project_id}/batch")
async def batch_operation(
    project_id: str,
    request: BatchOperationRequest,
    codebase: Codebase = Depends(get_codebase)
):
    try:
        results = []
        
        # Map operation to method
        operations = {
            "replace_text": lambda file, params: file.replace_text(
                params["pattern"], params["replacement"]
            ),
            "add_import": lambda file, params: file.add_import(
                params["import_statement"]
            ),
            "remove_import": lambda file, params: file.remove_import(
                params["import_statement"]
            ),
        }
        
        if request.operation not in operations:
            raise ValueError(f"Unknown batch operation: {request.operation}")
        
        # Execute the operation on each file
        for file_path in request.files:
            file = codebase.get_file(file_path)
            result = operations[request.operation](file, request.params)
            results.append({
                "file": file_path,
                "result": str(result)
            })
        
        # Commit changes
        codebase.commit()
        
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/projects/{project_id}/analysis")
async def analyze_codebase(
    project_id: str,
    request: AnalysisRequest,
    codebase: Codebase = Depends(get_codebase)
):
    try:
        # Map analysis type to function
        analysis_types = {
            "complexity": lambda target, params: analyze_complexity(
                codebase.get_file(target) if target else codebase
            ),
            "dependencies": lambda target, params: analyze_dependencies(
                codebase.get_file(target) if target else codebase
            ),
            "imports": lambda target, params: {
                file.path: [imp for imp in file.imports] 
                for file in (
                    [codebase.get_file(target)] if target else codebase.files(extensions="*")
                ) if hasattr(file, "imports")
            },
            "metrics": lambda target, params: {
                "total_files": len(codebase.files(extensions="*")),
                "total_symbols": len(codebase.symbols),
                "total_classes": len(codebase.classes),
                "total_functions": len(codebase.functions),
                "lines_of_code": sum(len(file.content.splitlines()) for file in codebase.files(extensions="*")),
            }
        }
        
        if request.type not in analysis_types:
            raise ValueError(f"Unknown analysis type: {request.type}")
        
        # Execute the analysis
        result = analysis_types[request.type](request.target, request.params or {})
        
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/projects/{project_id}/git")
async def git_operation(
    project_id: str,
    request: GitOperationRequest,
    codebase: Codebase = Depends(get_codebase)
):
    try:
        # Map git operation to method
        operations = {
            "commit": lambda params: codebase.git_commit(params["message"]),
            "status": lambda params: codebase.git_status(),
            "checkout": lambda params: codebase.git_checkout(params["branch"]),
            "create_branch": lambda params: codebase.git_create_branch(params["branch"]),
            "pull": lambda params: codebase.git_pull(),
            "push": lambda params: codebase.git_push(),
        }
        
        if request.operation not in operations:
            raise ValueError(f"Unknown git operation: {request.operation}")
        
        # Execute the operation
        result = operations[request.operation](request.params)
        
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_id}/dependencies")
async def get_dependencies(project_id: str, codebase: Codebase = Depends(get_codebase)):
    try:
        # Get all symbols and their dependencies
        dependencies = []
        
        for symbol in codebase.symbols:
            if hasattr(symbol, "dependencies"):
                for dep in symbol.dependencies:
                    dependencies.append({
                        "source": {
                            "name": symbol.name,
                            "type": symbol.symbol_type.name,
                            "file_path": symbol.file.path,
                        },
                        "target": {
                            "name": dep.name,
                            "type": dep.symbol_type.name,
                            "file_path": dep.file.path,
                        }
                    })
        
        return dependencies
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_id}/imports")
async def get_imports(project_id: str, codebase: Codebase = Depends(get_codebase)):
    try:
        imports = {}
        
        for file in codebase.files(extensions="*"):
            if hasattr(file, "imports"):
                imports[file.path] = [
                    {
                        "module": imp.module,
                        "name": imp.name,
                        "alias": imp.alias,
                        "is_relative": imp.is_relative
                    }
                    for imp in file.imports
                ]
        
        return imports
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# WebSocket connection for real-time updates
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await websocket.accept()
    
    # Register the connection
    if project_id not in active_connections:
        active_connections[project_id] = []
    active_connections[project_id].append(websocket)
    
    try:
        while True:
            # Keep the connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        # Remove the connection when disconnected
        active_connections[project_id].remove(websocket)

# Function to broadcast updates to all connected clients
async def broadcast_update(project_id: str, message: dict):
    if project_id in active_connections:
        for connection in active_connections[project_id]:
            await connection.send_json(message)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)