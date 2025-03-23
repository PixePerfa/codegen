"""Main application for the integrated CI/CD flow.

This module integrates all components of the CI/CD flow and provides
a unified interface for deployment.
"""

import logging
import os
from typing import Any, Dict

import modal
from codegen.extensions.events.codegen_app import CodegenApp
from fastapi import FastAPI, Request

from development_engine import create_development_engine
from knowledge_assistant import create_knowledge_assistant
from requirements_hub import create_requirements_hub
from review_system import create_review_system
from shared import get_modal_image, get_modal_secret, load_config_from_env

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create Modal image and app
image = get_modal_image()
app = CodegenApp(name="codegen-cicd")


@app.cls(secrets=[get_modal_secret()], keep_warm=1, image=image)
class IntegratedCICDFlow:
    """Integrated CI/CD flow for Codegen."""

    def __init__(self):
        """Initialize the integrated CI/CD flow."""
        self.config = None
        self.requirements_hub = None
        self.development_engine = None
        self.review_system = None
        self.knowledge_assistant = None
        self.web_app = None

    @modal.enter()
    def setup(self):
        """Set up the integrated CI/CD flow."""
        logger.info("Setting up integrated CI/CD flow")
        
        # Load configuration
        self.config = load_config_from_env()
        
        # Initialize components
        self.requirements_hub = create_requirements_hub(app)
        self.development_engine = create_development_engine()
        self.review_system = create_review_system()
        self.knowledge_assistant = create_knowledge_assistant()
        
        # Create FastAPI app
        self.web_app = self.create_fastapi_app()
        
        # Subscribe to Linear webhooks
        app.linear.subscribe_all_handlers()
        
        logger.info("Integrated CI/CD flow set up successfully")

    @modal.exit()
    def teardown(self):
        """Clean up resources."""
        logger.info("Tearing down integrated CI/CD flow")
        
        # Unsubscribe from Linear webhooks
        app.linear.unsubscribe_all_handlers()

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
            return app.github.handle(event, request)
        
        # Add Linear webhook endpoint
        @web_app.post("/linear/webhook")
        async def linear_webhook(request: Request):
            """Handle Linear webhook events."""
            event = await request.json()
            return app.linear.handle(event, request)
        
        # Add health check endpoint
        @web_app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok"}
        
        return web_app

    @modal.method()
    def process_linear_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Linear event.

        Args:
            event: Linear webhook event

        Returns:
            Response data
        """
        logger.info(f"Processing Linear event: {event.get('action')}")
        return app.linear.handle(event)

    @modal.method()
    def process_github_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a GitHub event.

        Args:
            event: GitHub webhook event

        Returns:
            Response data
        """
        logger.info(f"Processing GitHub event: {event.get('action')}")
        return app.github.handle(event)

    @modal.web_endpoint(method="GET")
    def index(self):
        """Index page."""
        return {
            "name": "Codegen Integrated CI/CD Flow",
            "version": "1.0.0",
            "endpoints": {
                "linear_webhook": "/linear/webhook",
                "github_webhook": "/github/webhook",
                "slack": "/slack",
                "health": "/health",
            },
        }

    @modal.web_endpoint(method="POST")
    def webhook(self, request: Request):
        """Generic webhook endpoint that routes to the appropriate handler."""
        # Get the webhook source from the path
        path = request.url.path
        if "linear" in path:
            return self.process_linear_event(request.json())
        elif "github" in path:
            return self.process_github_event(request.json())
        else:
            return {"error": "Unknown webhook source"}


if __name__ == "__main__":
    # For local development
    modal.runner.deploy_in_background(app)