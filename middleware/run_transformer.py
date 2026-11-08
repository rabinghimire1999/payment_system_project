# middleware/run_transformer.py
import uvicorn
import os
import sys

from backend.core.logger import setup_app_logging

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "transformer.api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",  
    )