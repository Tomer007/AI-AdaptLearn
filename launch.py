#!/usr/bin/env python3
"""
AI-AdaptLearn Launcher Script
This script sets the correct Python path and launches the application.
"""

import os
import sys
import warnings
try:
    from urllib3.exceptions import NotOpenSSLWarning
except Exception:  # pragma: no cover
    NotOpenSSLWarning = None  # type: ignore

def main():
    """Launch the AI-AdaptLearn application."""
    
    # Get the current directory (where this script is located)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the current directory to Python path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    print("🚀 Launching AI-AdaptLearn...")
    print(f"📍 Working directory: {current_dir}")
    print(f"🐍 Python path: {sys.path[0]}")
    
    try:
        # Suppress noisy third-party warnings on startup
        # Ensure suppression applies in uvicorn reloader subprocess as well
        existing_filters = os.environ.get("PYTHONWARNINGS", "")
        extra_filters = [
            "ignore::urllib3.exceptions.NotOpenSSLWarning",
            "ignore:As of langchain-core 0.3.0",
            "ignore:Valid config keys have changed in V2",
        ]
        os.environ["PYTHONWARNINGS"] = ",".join([f for f in [existing_filters] + extra_filters if f])
        if NotOpenSSLWarning:
            warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
        warnings.filterwarnings("ignore", message=r".*LangChainDeprecationWarning.*")
        warnings.filterwarnings("ignore", message=r".*As of langchain-core 0.3.0.*")
        warnings.filterwarnings("ignore", message=r".*Valid config keys have changed in V2.*")

        # Import and run the app
        from app.main import app
        import uvicorn  
        
        print("✅ Application imported successfully!")
        print("🌟 Starting server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/api/docs")
        print("🔍 Health Check: http://localhost:8000/health")
        print("")
        print("Press Ctrl+C to stop the server")
        print("")
        
        # Run the app
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you have installed all dependencies:")
        print("   pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
