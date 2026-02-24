import subprocess
import sys
import time
import os

def kill_port(port):
    """Kill process on a specific port (Windows)."""
    try:
        # Use findstr to get PIDs for the port
        output = subprocess.check_output(f"netstat -ano | findstr LISTENING | findstr :{port}", shell=True).decode()
        pids = set()
        for line in output.strip().split('\n'):
            parts = line.split()
            if len(parts) > 4:
                pids.add(parts[-1])
        
        for pid in pids:
            print(f"🔥 Cleaning up port {port} (PID: {pid})...")
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
        
        if pids:
            time.sleep(1) # Give OS time to release the port
    except:
        pass

def find_python(directory, venv_name="venv"):
    """Locate the python executable in a virtual environment."""
    if os.name == 'nt': # Windows
        python_path = os.path.join(directory, venv_name, "Scripts", "python.exe")
    else: # Linux/Mac
        python_path = os.path.join(directory, venv_name, "bin", "python")
    
    if os.path.exists(python_path):
        return python_path
    return sys.executable

def run_servers():
    print("🚀 Starting AI Sign Assistant Unified App...")
    
    # Pre-startup cleanup
    kill_port(8000)
    kill_port(3005)
    kill_port(3003)
    
    root_dir = os.getcwd()
    django_dir = os.path.join(root_dir, "Voice2sign")
    fastapi_dir = os.path.join(root_dir, "Automated-Sign-Language-Tutor")
    
    # Use specific venvs for each part
    django_python = find_python(django_dir)
    fastapi_python = find_python(root_dir) # FastAPI uses root venv
    
    print(f"🐍 Django Python: {django_python}")
    print(f"🐍 Signer Python: {fastapi_python}")
    
    # 1. Start Sign-to-Voice Backend
    print("📡 Starting Sign-to-Voice Backend (Signer)...")
    fastapi_proc = subprocess.Popen(
        [fastapi_python, "server_signer.py"],
        cwd=root_dir
    )
    
    # Wait a bit for FastAPI to initialize
    time.sleep(2)
    
    # 2. Start Django Frontend
    print("🌐 Starting Main Dashboard (Django)...")
    django_proc = subprocess.Popen(
        [django_python, "manage.py", "runserver", "0.0.0.0:8000"],
        cwd=django_dir
    )
    
    print("\n✅ Both services are running!")
    print("🔗 Dashboard: http://localhost:8000")
    print("🔗 Signer API: http://localhost:3005")
    print("\nPress Ctrl+C to stop both servers.")
    
    try:
        while True:
            time.sleep(1)
            if django_proc.poll() is not None or fastapi_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
    finally:
        django_proc.terminate()
        fastapi_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    run_servers()
