"""Main application for the integrated CI/CD flow."""

import asyncio
import logging
import os
from typing import Dict

import modal
from codegen.extensions.events.codegen_app import CodegenApp
from fastapi import FastAPI, Request

from event_bus import event_bus
from events import (
    handle_github_webhook,
    handle_linear_webhook,
    handle_slack_webhook,
    setup_event_handlers,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the base image with dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        # Codegen
        "codegen>=0.22.2",
        # Other dependencies
        "openai>=1.1.0",
        "fastapi[standard]",
        "slack_sdk",
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
    )
)

# Create the CodegenApp
app = CodegenApp(name="integrated-cicd-flow")

# Create the FastAPI app
fastapi_app = FastAPI(title="Integrated CI/CD Flow")


@fastapi_app.on_event("startup")
async def startup_event():
    """Start the event bus on startup."""
    logger.info("Starting event bus")
    # Set up event handlers
    await setup_event_handlers()
    # Start the event bus
    asyncio.create_task(event_bus.start())


@fastapi_app.on_event("shutdown")
async def shutdown_event():
    """Stop the event bus on shutdown."""
    logger.info("Stopping event bus")
    await event_bus.stop()


@fastapi_app.post("/linear/events")
async def linear_events(request: Request):
    """Handle Linear webhook events."""
    data = await request.json()
    logger.info("Received Linear webhook event")
    handle_linear_webhook(data)
    return {"status": "success"}


@fastapi_app.post("/github/events")
async def github_events(request: Request):
    """Handle GitHub webhook events."""
    data = await request.json()
    logger.info("Received GitHub webhook event")
    handle_github_webhook(data)
    return {"status": "success"}


@fastapi_app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack webhook events."""
    data = await request.json()
    logger.info("Received Slack webhook event")
    handle_slack_webhook(data)
    return {"status": "success"}


# Modal deployment
modal_app = modal.App("integrated-cicd-flow")


@modal_app.function(
    image=base_image,
    secrets=[modal.Secret.from_dotenv()],
    keep_warm=1,
)
@modal.asgi_app()
def serve():
    """Serve the FastAPI app with Modal."""
    return fastapi_app


if __name__ == "__main__":
    # For local development
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)