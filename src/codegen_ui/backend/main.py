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

# Import our new modules
from .code_quality import analyze_code_quality
from .refactoring import generate_refactoring_suggestions
from .test_generation import generate_tests
from .documentation import generate_documentation
from .visualization import generate_visualizations
from .initialization import initialize_codebase, detect_wsl_path, get_system_info, scan_for_projects

app = FastAPI(title="Codegen UI API", description="API for the Codegen UI")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, in production this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)