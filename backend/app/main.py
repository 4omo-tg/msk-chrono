from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from app.core.config import settings
from app.api.v1.api import api_router
from app.web.admin import router as admin_router

from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend for Moscow Chrono Walker - Historical Exploration Game",
    version="0.1.0"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads dir exists
UPLOADS_DIR = os.environ.get("UPLOADS_DIR", "uploads")
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Frontend dist directory - check multiple locations
FRONTEND_PATHS = [
    "/app/frontend_dist",  # Docker container
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist"),  # Local dev
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend_dist"),  # Relative
]

FRONTEND_DIR = None
for path in FRONTEND_PATHS:
    if os.path.exists(path) and os.path.isdir(path):
        FRONTEND_DIR = path
        break

print(f"Frontend dir: {FRONTEND_DIR}")

# Mount uploads
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Mount frontend assets if available
if FRONTEND_DIR and os.path.exists(os.path.join(FRONTEND_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="frontend_assets")

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix="/admin")


# Serve frontend for all non-API routes (SPA fallback)
@app.get("/{full_path:path}")
async def serve_frontend(request: Request, full_path: str):
    # Skip API and admin routes
    if full_path.startswith("api/") or full_path.startswith("admin/") or full_path.startswith("uploads/") or full_path.startswith("assets/") or full_path.startswith("docs") or full_path.startswith("openapi"):
        return {"detail": "Not Found"}
    
    if not FRONTEND_DIR:
        return {"message": "Welcome to Moscow Chrono Walker API", "docs": "/docs"}
    
    # Try to serve static file first
    file_path = os.path.join(FRONTEND_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Fallback to index.html for SPA routing
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"message": "Welcome to Moscow Chrono Walker API", "docs": "/docs"}
