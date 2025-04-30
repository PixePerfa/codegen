"""
Enhanced CI/CD Flow - Main Application

This module integrates all components of the enhanced CI/CD flow and provides
a unified interface for deployment.
"""

import logging
import os
from typing import Dict, List, Optional

import modal
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from codegen import CodegenApp, Codebase
from config import MODAL_DEPLOYMENT, get_component_config

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Codegen app
cg = CodegenApp(
    name=MODAL_DEPLOYMENT["app_name"],
    repo=os.environ.get("REPO_NAME", "codegen-sh/codegen-sdk"),
)

# Import components
from components.ticket_handler import register_ticket_handlers
from components.code_analyzer import register_code_analyzer
from components.pr_validator import register_pr_validators
from components.integration_hub import register_integration_handlers

# Register component handlers
if get_component_config("ticket_handler")["enabled"]:
    register_ticket_handlers(cg)

if get_component_config("code_analyzer")["enabled"]:
    register_code_analyzer(cg)

if get_component_config("pr_validator")["enabled"]:
    register_pr_validators(cg)

if get_component_config("integration_hub")["enabled"]:
    register_integration_handlers(cg)


# Create Modal image
base_image = (
    modal.Image.debian_slim(python_version=MODAL_DEPLOYMENT["python_version"])
    .apt_install("git")
    .pip_install(
        "codegen",
        "fastapi[standard]",
        "slack_sdk",
        "networkx",
        "rich",
        "rich-click",
        "langchain",
        "langchain-core",
    )
)

# Create Modal app
app = modal.App(MODAL_DEPLOYMENT["app_name"])


@app.function(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
    keep_warm=MODAL_DEPLOYMENT["keep_warm"],
)
@modal.asgi_app()
def fastapi_app():
    """Create and return the FastAPI app for Modal deployment."""
    logger.info(f"Starting {MODAL_DEPLOYMENT['app_name']} FastAPI app")
    return cg.app


if __name__ == "__main__":
    # If running locally, use uvicorn to serve the app
    import uvicorn
    from config import API_SETTINGS

    uvicorn.run(
        "app:cg.app",
        host=API_SETTINGS["host"],
        port=API_SETTINGS["port"],
        reload=API_SETTINGS["debug"],
    )