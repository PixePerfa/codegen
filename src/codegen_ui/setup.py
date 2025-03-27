import os
import subprocess
import sys
from pathlib import Path

def setup_backend():
    """Set up the backend dependencies."""
    print("Setting up backend dependencies...")
    
    # Check if FastAPI is installed
    try:
        import fastapi
        print("FastAPI is already installed.")
    except ImportError:
        print("Installing FastAPI and dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn[standard]", "pydantic"])
    
    print("Backend setup complete.")

def setup_frontend():
    """Set up the frontend dependencies."""
    print("Setting up frontend dependencies...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Check if node_modules exists
    if (frontend_dir / "node_modules").exists():
        print("Frontend dependencies already installed.")
    else:
        print("Installing frontend dependencies...")
        os.chdir(frontend_dir)
        subprocess.check_call(["npm", "install"])
    
    print("Frontend setup complete.")

def run_backend():
    """Run the backend server."""
    print("Starting backend server...")
    
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Run the backend server
    subprocess.check_call([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

def run_frontend():
    """Run the frontend development server."""
    print("Starting frontend development server...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    # Run the frontend development server
    subprocess.check_call(["npm", "start"])

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python setup.py [setup|backend|frontend|all]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "setup":
        setup_backend()
        setup_frontend()
    elif command == "backend":
        run_backend()
    elif command == "frontend":
        run_frontend()
    elif command == "all":
        # Start both servers in separate processes
        import threading
        
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # Give the backend a moment to start
        import time
        time.sleep(2)
        
        # Run the frontend (this will block until it exits)
        run_frontend()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python setup.py [setup|backend|frontend|all]")
        sys.exit(1)

if __name__ == "__main__":
    main()