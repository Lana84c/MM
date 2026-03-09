from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "page_title": "MM | Modern Manners LMS",
            "app_name": "MM",
        },
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}