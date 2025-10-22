#!/usr/bin/env python3
"""
Quick start script for Transaction Risk Analytics API
This script helps users get started quickly by checking dependencies and starting the server
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        if env_example_path.exists():
            print("⚠️  .env file not found")
            print("📝 Please copy .env.example to .env and configure your settings:")
            print("   cp .env.example .env")
            return False
        else:
            print("❌ Neither .env nor .env.example found")
            return False
    
    # Check for required variables
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = []
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
            for var in required_vars:
                if f"{var}=" not in content or f"{var}=your-" in content:
                    missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing or unconfigured environment variables: {', '.join(missing_vars)}")
            print("Please update your .env file with actual values")
            return False
        
        print("✅ Environment configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Check if requirements.txt exists
        if not Path("requirements.txt").exists():
            print("❌ requirements.txt not found")
            return False
        
        # Install dependencies
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def run_tests():
    """Run setup tests"""
    print("🧪 Running setup tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_setup.py"], 
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Transaction Risk Analytics API...")
    
    try:
        # Get host and port from environment or use defaults
        host = os.getenv("HOST", "0.0.0.0")
        port = os.getenv("PORT", "8000")
        
        print(f"🌐 Server will start on http://{host}:{port}")
        print(f"📚 API docs will be available at http://{host}:{port}/docs")
        print(f"📖 ReDoc will be available at http://{host}:{port}/redoc")
        print("\nPress Ctrl+C to stop the server\n")
        
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", "app:app",
            "--host", host,
            "--port", port,
            "--reload"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")


def main():
    """Main startup sequence"""
    print("🚀 Transaction Risk Analytics API - Quick Start")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check environment configuration
    env_ok = check_env_file()
    
    # Install dependencies
    deps_ok = install_dependencies()
    if not deps_ok:
        print("\n❌ Failed to install dependencies. Please run manually:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Run tests
    print("\n" + "=" * 50)
    tests_ok = run_tests()
    
    if not tests_ok:
        print("\n⚠️  Some tests failed, but you can still try to start the server")
    
    if not env_ok:
        print("\n⚠️  Environment not fully configured. Please update .env file before starting.")
        response = input("Do you want to start anyway? (y/N): ").lower().strip()
        if response != 'y':
            print("Please configure your .env file and run again")
            sys.exit(1)
    
    # Start server
    print("\n" + "=" * 50)
    start_server()


if __name__ == "__main__":
    main()
