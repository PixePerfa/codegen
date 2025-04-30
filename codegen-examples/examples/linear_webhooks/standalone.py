import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import uvicorn
from codegen.extensions.events.codegen_app import CodegenApp

# Load environment variables from .env file
load_dotenv()

# Initialize the CodegenApp
app = CodegenApp(name="test-linear")

# Create a FastAPI app
fastapi_app = app.app

@fastapi_app.post("/linear/events")
async def handle_linear_event(request: Request):
    """Handle incoming Linear events."""
    payload = await request.json()
    print(f"Received Linear event: {payload}")
    return await app.linear.handle(payload)

# Verify required environment variables
required_vars = ["LINEAR_ACCESS_TOKEN", "LINEAR_SIGNING_SECRET", "LINEAR_TEAM_ID"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please create a .env file with the following variables:")
    print("\n".join([f"{var}=\"your_{var.lower()}\"" for var in required_vars]))
    exit(1)

if __name__ == "__main__":
    print("Starting Linear webhook server...")
    print("Listening for Linear events at: http://0.0.0.0:8000/linear/events")
    print("Use a tool like ngrok to expose this endpoint to the internet.")
    print("Then configure your Linear webhook to point to: https://your-ngrok-url/linear/events")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)