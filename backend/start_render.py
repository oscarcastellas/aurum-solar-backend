#!/usr/bin/env python3
"""
Render.com startup script for Aurum Solar FastAPI backend
"""

import os
import uvicorn
from main_simple import app

if __name__ == "__main__":
    # Get port from Render environment variable
    port = int(os.environ.get("PORT", 10000))
    
    # Start the server
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        workers=1
    )
