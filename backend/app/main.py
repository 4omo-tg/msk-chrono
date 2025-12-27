from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
if hasattr(settings, "BACKEND_CORS_ORIGINS") and settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
elif True:
    # Fallback for dev if settings not loaded correctly or empty
     app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Ensure uploads dir exists
if not os.path.exists("app/uploads"):
    os.makedirs("app/uploads")

app.mount("/static", StaticFiles(directory="app/uploads"), name="static")

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix="/admin")


@app.get("/")
async def root():
    return {"message": "Welcome to Moscow Chrono Walker API"}
