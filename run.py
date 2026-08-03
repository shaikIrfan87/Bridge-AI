"""
Server Launcher with Setup
Integrates batch-like setup and starts the FastAPI server
"""

import os
import sys
import subprocess
import time
import webbrowser
import socket
from pathlib import Path

# Ensure we're in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import uvicorn
from app.core import settings


def kill_port_process(port):
    """Kill any existing process using the specified port."""
    try:
        if sys.platform == "win32":
            # Windows: use netstat and taskkill
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                # Extract PID from netstat output (last column)
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) > 0:
                        pid = parts[-1]
                        try:
                            subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                            print(f"[OK] Killed process {pid} using port {port}")
                        except:
                            pass
        else:
            # Unix/Linux: use lsof and kill
            result = subprocess.run(
                f'lsof -i :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        try:
                            os.kill(int(pid), 9)
                            print(f"[OK] Killed process {pid} using port {port}")
                        except:
                            pass
    except Exception as e:
        print(f"[INFO] Could not kill existing process on port {port}: {e}")
    
    # Wait a moment for port to be released
    time.sleep(1)


def check_python():
    """Verify Python is installed and accessible."""
    try:
        subprocess.run([sys.executable, "--version"], capture_output=True, check=True)
        print("[OK] Python detected")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] Python is not installed or not in PATH")
        print("Please install Python and try again")
        return False


def setup_virtual_environment():
    """Create and setup virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print(f"Setting up virtual environment at {venv_path}...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("[OK] Virtual environment created")
            
            # Upgrade pip
            venv_python = str(venv_path / ("Scripts" if sys.platform == "win32" else "bin") / "python")
            subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
            print("[OK] Pip upgraded")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to setup virtual environment: {e}")
            return False
    else:
        print("[OK] Virtual environment already exists")
    
    return True


def sync_dependencies():
    """Install/sync dependencies from requirements.txt."""
    print("Syncing dependencies from requirements.txt...")
    try:
        venv_path = Path("venv")
        venv_python = str(venv_path / ("Scripts" if sys.platform == "win32" else "bin") / "python")
        
        # Use current Python if venv doesn't exist or as fallback
        python_exe = sys.executable if not venv_path.exists() else venv_python
        
        subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("[OK] Dependencies synced")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to sync dependencies: {e}")
        return False


def open_browser():
    """Open browser to the application after server starts."""
    def delayed_open():
        time.sleep(4)  # Wait 4 seconds for server to start
        try:
            webbrowser.open(f"http://localhost:{settings.API_PORT}")
            print(f"[OK] Browser opened to http://localhost:{settings.API_PORT}")
        except Exception as e:
            print(f"[INFO] Could not open browser automatically: {e}")
    
    # Run in background thread
    import threading
    thread = threading.Thread(target=delayed_open, daemon=True)
    thread.start()


def print_startup_banner():
    """Print startup banner."""
    banner = """
==========================================
Starting Skill Assessment System...
==========================================
"""
    print(banner)


def main():
    """Main entry point with full setup."""
    print_startup_banner()
    
    # Check Python installation
    if not check_python():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Sync dependencies
    if not sync_dependencies():
        sys.exit(1)
    
    # Kill any existing process using the port
    print(f"Checking for existing processes on port {settings.API_PORT}...")
    kill_port_process(settings.API_PORT)
    
    # Open browser in background
    print("Starting the FastAPI application...")
    open_browser()
    
    # Start FastAPI server with socket reuse
    try:
        config = uvicorn.Config(
            "app.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.API_RELOAD,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Allow address reuse
        server.socket_options = [
            (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),
            (socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) if hasattr(socket, 'SO_REUSEPORT') else None
        ]
        server.socket_options = [opt for opt in server.socket_options if opt is not None]
        
        # Run server
        import asyncio
        asyncio.run(server.serve())
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
