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
    version="0.1.0",
    redirect_slashes=True,
)


@app.middleware("http")
async def normalize_api_path(request: Request, call_next):
    """Normalize API paths by stripping trailing slashes.
    This prevents FastAPI from issuing 307 redirects that lose
    Authorization headers in the browser."""
    path = request.scope["path"]
    if path.startswith("/api/") and len(path) > 5 and path.endswith("/"):
        request.scope["path"] = path.rstrip("/")
    return await call_next(request)


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

# SPA fallback — serve index.html for frontend routes
# Must be AFTER all API/admin routers
if FRONTEND_DIR:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import Response as StarletteResponse
    import mimetypes

    class SPAMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            # If the response is 404 and it's NOT an API/admin/docs request,
            # serve the SPA index.html instead
            path = request.url.path
            if (
                response.status_code == 404
                and request.method == "GET"
                and not path.startswith("/api/")
                and not path.startswith("/admin")
                and not path.startswith("/docs")
                and not path.startswith("/openapi")
                and not path.startswith("/uploads/")
            ):
                # Try static file first
                file_path = os.path.join(FRONTEND_DIR, path.lstrip("/"))
                if os.path.isfile(file_path):
                    return FileResponse(file_path)
                # SPA fallback
                index_path = os.path.join(FRONTEND_DIR, "index.html")
                if os.path.exists(index_path):
                    return FileResponse(index_path)
            return response

    app.add_middleware(SPAMiddleware)

    # Serve root
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
