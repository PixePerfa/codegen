"""Standalone version of the integrated CI/CD flow.

This module provides a standalone version of the integrated CI/CD flow
that can be run locally without Modal.
"""

import logging
import os
from typing import Any, Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from development_engine import create_development_engine
from knowledge_assistant import create_knowledge_assistant
from requirements_hub import create_requirements_hub
from review_system import create_review_system
from shared import load_config_from_env

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class StandaloneApp:
    """Standalone version of the integrated CI/CD flow."""

    def __init__(self):
        """Initialize the standalone app."""
        self.config = None
        self.requirements_hub = None
        self.development_engine = None
        self.review_system = None
        self.knowledge_assistant = None
        self.web_app = None

    def setup(self):
        """Set up the standalone app."""
        logger.info("Setting up standalone app")
        
        # Load configuration
        self.config = load_config_from_env()
        
        # Initialize components
        # Note: In standalone mode, we don't have a CodegenApp instance
        # so we'll need to mock it or adapt the components
        self.development_engine = create_development_engine()
        self.review_system = create_review_system()
        self.knowledge_assistant = create_knowledge_assistant()
        
        # Create FastAPI app
        self.web_app = self.create_fastapi_app()
        
        logger.info("Standalone app set up successfully")
        
        return self.web_app

    def create_fastapi_app(self) -> FastAPI:
        """Create a FastAPI app with all webhook handlers.

        Returns:
            FastAPI app
        """
        web_app = FastAPI()
        
        # Create Slack app
        slack_app = self.knowledge_assistant.create_fastapi_app()
        
        # Mount Slack app
        web_app.mount("/slack", slack_app)
        
        # Add GitHub webhook endpoint
        @web_app.post("/github/webhook")
        async def github_webhook(request: Request):
            """Handle GitHub webhook events."""
            event = await request.json()
            logger.info(f"Received GitHub webhook: {event.get('action')}")
            # In standalone mode, we'll just log the event
            return {"status": "ok"}
        
        # Add Linear webhook endpoint
        @web_app.post("/linear/webhook")
        async def linear_webhook(request: Request):
            """Handle Linear webhook events."""
            event = await request.json()
            logger.info(f"Received Linear webhook: {event.get('action')}")
            # In standalone mode, we'll just log the event
            return {"status": "ok"}
        
        # Add health check endpoint
        @web_app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok"}
        
        # Add index page
        @web_app.get("/")
        async def index():
            """Index page."""
            return {
                "name": "Codegen Integrated CI/CD Flow (Standalone)",
                "version": "1.0.0",
                "endpoints": {
                    "linear_webhook": "/linear/webhook",
                    "github_webhook": "/github/webhook",
                    "slack": "/slack",
                    "health": "/health",
                },
            }
        
        return web_app


def create_app() -> FastAPI:
    """Create and set up the standalone app.

    Returns:
        FastAPI app
    """
    app = StandaloneApp()
    return app.setup()


if __name__ == "__main__":
    # Create the app
    app = create_app()
    
    # Run the app
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)