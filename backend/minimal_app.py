"""
Minimal FastAPI app for Railway deployment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI(title="Aurum Solar API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Aurum Solar API is running!", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "aurum-solar-api"}

@app.get("/api/v1/health")
async def api_health():
    return {"status": "healthy", "endpoint": "api-health"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
