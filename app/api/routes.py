from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.db import engine
from app.models.course import Course
from app.models.user import User
from app.services.ai_coach import get_lesson_coaching_response
from app.services.auth_service import authenticate_user
from app.services.course_service import (
    enroll_user_in_course,
    get_completed_lesson_ids_for_course,
    get_course_by_id,
    get_course_by_slug,
    get_course_progress_percent,
    get_lesson_by_slug,
    get_published_courses,
    get_user_enrolled_courses,
    is_lesson_complete,
    is_user_enrolled_in_course,
    mark_lesson_complete,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    current_user = get_current_user(request, db)
    courses = get_published_courses(db)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "page_title": "MM | Modern Manners LMS",
            "app_name": "MM",
            "current_user": current_user,
            "courses": courses,
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    current_user = get_current_user(request, db)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "page_title": "Login | MM",
            "error": None,
            "current_user": current_user,
        },
    )


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = authenticate_user(db, email, password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "page_title": "Login | MM",
                "error": "Invalid email or password.",
                "current_user": None,
            },
            status_code=400,
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    enrolled_courses = get_user_enrolled_courses(db, current_user)
    course_cards = [
        {
            "course": course,
            "progress_percent": get_course_progress_percent(db, current_user, course),
            "lesson_count": len(course.lessons),
        }
        for course in enrolled_courses
    ]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "page_title": "Dashboard | MM",
            "current_user": current_user,
            "course_cards": course_cards,
        },
    )


@router.post("/courses/{course_id}/enroll")
async def enroll_in_course(
    course_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    course = get_course_by_id(db, course_id)
    if course:
        enroll_user_in_course(db, current_user, course)

    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/courses/{course_slug}", response_class=HTMLResponse)
async def course_detail(
    course_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    current_user = get_current_user(request, db)
    course = get_course_by_slug(db, course_slug)

    if not course:
        return templates.TemplateResponse(
            "not_found.html",
            {
                "request": request,
                "page_title": "Not Found | MM",
                "current_user": current_user,
                "message": "Course not found.",
            },
            status_code=404,
        )

    enrolled = current_user is not None and is_user_enrolled_in_course(db, current_user, course)
    completed_lesson_ids = (
        get_completed_lesson_ids_for_course(db, current_user, course) if current_user and enrolled else set()
    )
    progress_percent = (
        get_course_progress_percent(db, current_user, course) if current_user and enrolled else 0
    )

    lessons = sorted(course.lessons, key=lambda lesson: lesson.sort_order)

    return templates.TemplateResponse(
        "course_detail.html",
        {
            "request": request,
            "page_title": f"{course.title} | MM",
            "current_user": current_user,
            "course": course,
            "lessons": lessons,
            "enrolled": enrolled,
            "completed_lesson_ids": completed_lesson_ids,
            "progress_percent": progress_percent,
        },
    )


@router.get("/lessons/{lesson_slug}", response_class=HTMLResponse)
async def lesson_detail(
    lesson_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    current_user = get_current_user(request, db)
    lesson = get_lesson_by_slug(db, lesson_slug)

    if not lesson:
        return templates.TemplateResponse(
            "not_found.html",
            {
                "request": request,
                "page_title": "Not Found | MM",
                "current_user": current_user,
                "message": "Lesson not found.",
            },
            status_code=404,
        )

    course = lesson.course
    enrolled = current_user is not None and is_user_enrolled_in_course(db, current_user, course)
    completed = current_user is not None and enrolled and is_lesson_complete(db, current_user, lesson)

    return templates.TemplateResponse(
        "lesson_detail.html",
        {
            "request": request,
            "page_title": f"{lesson.title} | MM",
            "current_user": current_user,
            "lesson": lesson,
            "course": course,
            "enrolled": enrolled,
            "completed": completed,
            "coach_response": None,
            "coach_prompt": "",
        },
    )


@router.post("/lessons/{lesson_slug}/coach", response_class=HTMLResponse)
async def lesson_coach(
    lesson_slug: str,
    request: Request,
    coach_prompt: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    current_user = get_current_user(request, db)
    lesson = get_lesson_by_slug(db, lesson_slug)

    if not lesson:
        return templates.TemplateResponse(
            "not_found.html",
            {
                "request": request,
                "page_title": "Not Found | MM",
                "current_user": current_user,
                "message": "Lesson not found.",
            },
            status_code=404,
        )

    course = lesson.course
    enrolled = current_user is not None and is_user_enrolled_in_course(db, current_user, course)
    completed = current_user is not None and enrolled and is_lesson_complete(db, current_user, lesson)

    coach_response = None
    cleaned_prompt = coach_prompt.strip()

    if current_user and enrolled and cleaned_prompt:
        coach_response = get_lesson_coaching_response(
            lesson_title=lesson.title,
            lesson_content=lesson.content,
            user_message=cleaned_prompt,
        )

    return templates.TemplateResponse(
        "lesson_detail.html",
        {
            "request": request,
            "page_title": f"{lesson.title} | MM",
            "current_user": current_user,
            "lesson": lesson,
            "course": course,
            "enrolled": enrolled,
            "completed": completed,
            "coach_response": coach_response,
            "coach_prompt": cleaned_prompt,
        },
    )


@router.post("/lessons/{lesson_slug}/complete")
async def complete_lesson(
    lesson_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    lesson = get_lesson_by_slug(db, lesson_slug)
    if not lesson:
        return RedirectResponse(url="/dashboard", status_code=303)

    if is_user_enrolled_in_course(db, current_user, lesson.course):
        mark_lesson_complete(db, current_user, lesson)

    return RedirectResponse(url=f"/lessons/{lesson.slug}", status_code=303)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def health_db() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}