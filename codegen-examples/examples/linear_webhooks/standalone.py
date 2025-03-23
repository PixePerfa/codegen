"""
Standalone version of the Linear webhooks example that can be run without Modal.
This is useful for local development and testing.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import uvicorn
from codegen.extensions.events.codegen_app import CodegenApp

# Load environment variables from .env file
load_dotenv()

# Create the CodegenApp instance
app = CodegenApp(name="linear-webhook-standalone")

# Get the FastAPI app from the CodegenApp
fastapi_app = app.app

@fastapi_app.get("/")
async def root():
    return {"message": "Linear Webhook Server is running"}

@fastapi_app.post("/linear/webhook")
async def linear_webhook(request: Request):
    """Handle incoming Linear webhook events."""
    payload = await request.json()
    print(f"Received Linear webhook event: {payload}")
    return {"status": "success"}

def main():
    """Run the FastAPI application."""
    # Check if required environment variables are set
    required_vars = ["LINEAR_ACCESS_TOKEN", "LINEAR_SIGNING_SECRET", "LINEAR_TEAM_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment.")
        return
    
    print("Starting Linear webhook server...")
    print(f"LINEAR_TEAM_ID: {os.getenv('LINEAR_TEAM_ID')}")
    
    # Run the FastAPI application
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()