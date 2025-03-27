from typing import Dict, Any, Optional
import subprocess
import os
from pathlib import Path

def initialize_codebase(path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize a codebase with codegen init command.
    
    Args:
        path: Path to the codebase
        language: Optional language to specify
    
    Returns:
        Dict with initialization status and details
    """
    try:
        # Ensure the path exists
        if not os.path.exists(path):
            return {
                "success": False,
                "message": f"Path does not exist: {path}"
            }
        
        # Change to the directory
        os.chdir(path)
        
        # Build the command
        cmd = ["codegen", "init"]
        if language:
            cmd.extend(["--language", language])
        
        # Run the initialization command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Codebase initialized successfully",
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "message": f"Initialization failed: {result.stderr}",
                "output": result.stderr
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during initialization: {str(e)}"
        }

def detect_wsl_path(windows_path: str) -> Optional[str]:
    """
    Convert a Windows path to a WSL path if running in WSL.
    
    Args:
        windows_path: Windows-style path
    
    Returns:
        WSL path if running in WSL, None otherwise
    """
    try:
        # Check if running in WSL
        is_wsl = False
        if os.path.exists('/proc/version'):
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    is_wsl = True
        
        if not is_wsl:
            return None
        
        # Convert Windows path to WSL path
        if windows_path.startswith(('C:', 'c:')):
            # Remove drive letter and convert backslashes
            path = windows_path[2:].replace('\\', '/')
            return f"/mnt/c{path}"
        elif windows_path.startswith(('D:', 'd:')):
            path = windows_path[2:].replace('\\', '/')
            return f"/mnt/d{path}"
        elif windows_path.startswith(('E:', 'e:')):
            path = windows_path[2:].replace('\\', '/')
            return f"/mnt/e{path}"
        else:
            # Try to handle other drives or UNC paths
            return windows_path.replace('\\', '/')
    except Exception:
        return None

def get_system_info() -> Dict[str, Any]:
    """
    Get information about the system environment.
    
    Returns:
        Dict with system information
    """
    try:
        # Check if running in WSL
        is_wsl = False
        wsl_version = None
        
        if os.path.exists('/proc/version'):
            with open('/proc/version', 'r') as f:
                version_info = f.read().lower()
                if 'microsoft' in version_info:
                    is_wsl = True
                    if 'wsl2' in version_info:
                        wsl_version = 2
                    else:
                        wsl_version = 1
        
        # Get Python version
        python_version = sys.version
        
        # Get codegen version
        codegen_version = None
        try:
            result = subprocess.run(
                ["codegen", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                codegen_version = result.stdout.strip()
        except Exception:
            pass
        
        return {
            "is_wsl": is_wsl,
            "wsl_version": wsl_version,
            "python_version": python_version,
            "codegen_version": codegen_version,
            "platform": sys.platform
        }
    except Exception as e:
        return {
            "error": str(e)
        }

def scan_for_projects(base_path: str = None) -> Dict[str, Any]:
    """
    Scan for potential codegen projects in common locations.
    
    Args:
        base_path: Optional base path to start scanning from
    
    Returns:
        Dict with scan results
    """
    try:
        projects = []
        
        # Determine paths to scan
        paths_to_scan = []
        
        if base_path and os.path.exists(base_path):
            paths_to_scan.append(base_path)
        
        # Add common locations
        home = os.path.expanduser("~")
        paths_to_scan.extend([
            home,
            os.path.join(home, "projects"),
            os.path.join(home, "code"),
            os.path.join(home, "src"),
            os.path.join(home, "workspace"),
            os.path.join(home, "repos")
        ])
        
        # In WSL, add Windows user directories
        is_wsl = False
        if os.path.exists('/proc/version'):
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    is_wsl = True
        
        if is_wsl:
            windows_paths = [
                "/mnt/c/Users",
                "/mnt/d/Projects",
                "/mnt/c/Projects",
                "/mnt/c/Code"
            ]
            paths_to_scan.extend([p for p in windows_paths if os.path.exists(p)])
        
        # Scan for potential projects
        for path in paths_to_scan:
            if not os.path.exists(path):
                continue
                
            try:
                # Look for directories with common project indicators
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    
                    if not os.path.isdir(item_path):
                        continue
                    
                    # Check for common project indicators
                    indicators = [
                        ".git",
                        "setup.py",
                        "package.json",
                        "requirements.txt",
                        "pyproject.toml",
                        "Cargo.toml",
                        "go.mod",
                        ".codegen"
                    ]
                    
                    for indicator in indicators:
                        if os.path.exists(os.path.join(item_path, indicator)):
                            # Determine language based on files
                            language = None
                            if os.path.exists(os.path.join(item_path, "setup.py")) or os.path.exists(os.path.join(item_path, "requirements.txt")):
                                language = "python"
                            elif os.path.exists(os.path.join(item_path, "package.json")):
                                language = "typescript"
                            elif os.path.exists(os.path.join(item_path, "Cargo.toml")):
                                language = "rust"
                            elif os.path.exists(os.path.join(item_path, "go.mod")):
                                language = "go"
                            
                            projects.append({
                                "name": item,
                                "path": item_path,
                                "language": language,
                                "indicators": [ind for ind in indicators if os.path.exists(os.path.join(item_path, ind))]
                            })
                            break
            except Exception:
                # Skip directories we can't access
                continue
        
        return {
            "success": True,
            "projects": projects
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error scanning for projects: {str(e)}"
        }

# Add import for sys
import sys