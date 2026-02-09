from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/{full_path:path}", response_class=HTMLResponse)
async def admin_spa(request: Request, full_path: str = ""):
    """Serve the SPA admin panel for all admin routes."""
    return templates.TemplateResponse("admin_spa.html", {"request": request})
