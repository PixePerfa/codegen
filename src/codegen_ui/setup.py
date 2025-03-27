import os
import subprocess
import sys
import platform
from pathlib import Path

def is_wsl():
    """Check if running in Windows Subsystem for Linux."""
    if os.path.exists('/proc/version'):
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    return False

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
    host = "0.0.0.0"  # Listen on all interfaces
    port = 8000
    
    # If running in WSL, print a helpful message
    if is_wsl():
        print("\nRunning in WSL environment.")
        print("To access the UI from Windows, use: http://localhost:3000")
        print("The backend API will be available at: http://localhost:8000")
        print("If you encounter connection issues, you may need to:")
        print("1. Check your Windows firewall settings")
        print("2. Use the WSL IP address instead of localhost")
        
        # Try to get the WSL IP address
        try:
            import socket
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            print(f"WSL IP address: {ip_address}")
            print(f"Alternative backend URL: http://{ip_address}:{port}")
        except Exception:
            pass
    
    subprocess.check_call([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", host, "--port", str(port)])

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