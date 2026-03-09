from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.analytics_service import (
    get_course_enrollment_stats,
    get_lesson_completion_stats,
    get_lesson_struggle_stats,
    get_platform_stats,
    get_scenario_usage_stats,
    get_top_coach_questions,
)

from app.core.deps import get_db
from app.core.db import engine
from app.models.course import Course
from app.models.user import User
from app.services.ai_coach import get_lesson_coaching_response
from app.services.auth_service import authenticate_user
from app.services.coach_memory_service import (
    get_lesson_conversation,
    save_ai_message,
    save_user_message,
)
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
from app.services.evaluation_service import evaluate_roleplay_session
from app.services.roleplay_service import (
    get_roleplay_opening_response,
    get_roleplay_turn_response,
)
from app.services.simulation_service import (
    add_simulation_message,
    build_simulation_history,
    create_simulation_session,
    get_active_scenarios_for_lesson,
    get_scenario_by_id,
    get_simulation_messages,
    get_simulation_session,
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
        get_completed_lesson_ids_for_course(db, current_user, course)
        if current_user and enrolled
        else set()
    )
    progress_percent = (
        get_course_progress_percent(db, current_user, course)
        if current_user and enrolled
        else 0
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

    conversation = []
    if current_user:
        conversation = get_lesson_conversation(db, current_user.id, lesson.id)

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
            "conversation": conversation,
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

    cleaned_prompt = coach_prompt.strip()
    conversation = []
    coach_response = None

    if current_user and enrolled and cleaned_prompt:
        history = get_lesson_conversation(db, current_user.id, lesson.id)

        save_user_message(db, current_user.id, lesson.id, cleaned_prompt)

        coach_response = get_lesson_coaching_response(
            lesson_title=lesson.title,
            lesson_content=lesson.content,
            user_message=cleaned_prompt,
            history=history,
        )

        save_ai_message(db, current_user.id, lesson.id, coach_response.answer)
        conversation = get_lesson_conversation(db, current_user.id, lesson.id)
    elif current_user:
        conversation = get_lesson_conversation(db, current_user.id, lesson.id)

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
            "coach_prompt": "",
            "conversation": conversation,
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


@router.get("/lessons/{lesson_slug}/practice", response_class=HTMLResponse)
async def lesson_practice(
    lesson_slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

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

    if not is_user_enrolled_in_course(db, current_user, lesson.course):
        return RedirectResponse(url=f"/courses/{lesson.course.slug}", status_code=303)

    scenarios = get_active_scenarios_for_lesson(db, lesson.id)

    return templates.TemplateResponse(
        "practice_select.html",
        {
            "request": request,
            "page_title": f"Practice | {lesson.title}",
            "current_user": current_user,
            "lesson": lesson,
            "course": lesson.course,
            "scenarios": scenarios,
        },
    )


@router.post("/lessons/{lesson_slug}/practice/start")
async def start_practice(
    lesson_slug: str,
    request: Request,
    scenario_id: int = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    lesson = get_lesson_by_slug(db, lesson_slug)
    if not lesson:
        return RedirectResponse(url="/dashboard", status_code=303)

    if not is_user_enrolled_in_course(db, current_user, lesson.course):
        return RedirectResponse(url=f"/courses/{lesson.course.slug}", status_code=303)

    scenario = get_scenario_by_id(db, scenario_id)
    if not scenario or scenario.lesson_id != lesson.id:
        return RedirectResponse(url=f"/lessons/{lesson.slug}/practice", status_code=303)

    session = create_simulation_session(
        db=db,
        user=current_user,
        lesson_id=lesson.id,
        scenario_id=scenario.id,
    )

    opening = get_roleplay_opening_response(
        scenario_title=scenario.title,
        ai_role=scenario.ai_role,
        learner_objective=scenario.learner_objective,
    )

    add_simulation_message(db, session.id, "assistant", opening.answer)

    return RedirectResponse(url=f"/practice/{session.id}", status_code=303)


@router.get("/practice/{session_id}", response_class=HTMLResponse)
async def practice_session_view(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    session = get_simulation_session(db, session_id, current_user.id)
    if not session:
        return RedirectResponse(url="/dashboard", status_code=303)

    messages = get_simulation_messages(db, session.id)

    return templates.TemplateResponse(
        "practice_session.html",
        {
            "request": request,
            "page_title": "Practice Session | MM",
            "current_user": current_user,
            "session": session,
            "lesson": session.lesson,
            "course": session.lesson.course,
            "scenario": session.scenario,
            "messages": messages,
        },
    )


@router.post("/practice/{session_id}/message")
async def practice_session_message(
    session_id: int,
    request: Request,
    practice_message: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    session = get_simulation_session(db, session_id, current_user.id)
    if not session:
        return RedirectResponse(url="/dashboard", status_code=303)

    if session.status == "completed":
        return RedirectResponse(url=f"/practice/{session.id}", status_code=303)

    cleaned_message = practice_message.strip()
    if not cleaned_message:
        return RedirectResponse(url=f"/practice/{session.id}", status_code=303)

    add_simulation_message(db, session.id, "user", cleaned_message)

    history_messages = get_simulation_messages(db, session.id)
    history = build_simulation_history(history_messages)

    ai_reply = get_roleplay_turn_response(
        scenario_title=session.scenario.title,
        ai_role=session.scenario.ai_role,
        learner_objective=session.scenario.learner_objective,
        history=history,
        user_message=cleaned_message,
    )

    add_simulation_message(db, session.id, "assistant", ai_reply.answer)

    session.turn_count += 1
    db.commit()

    return RedirectResponse(url=f"/practice/{session.id}", status_code=303)


@router.post("/practice/{session_id}/complete")
async def complete_practice_session(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    session = get_simulation_session(db, session_id, current_user.id)
    if not session:
        return RedirectResponse(url="/dashboard", status_code=303)

    if session.status == "completed":
        return RedirectResponse(url=f"/practice/{session.id}", status_code=303)

    messages = get_simulation_messages(db, session.id)
    history = build_simulation_history(messages)

    evaluation = evaluate_roleplay_session(
        scenario_title=session.scenario.title,
        ai_role=session.scenario.ai_role,
        learner_objective=session.scenario.learner_objective,
        messages=history,
    )

    session.status = "completed"
    session.score = evaluation.score
    session.feedback_summary = evaluation.feedback_summary
    db.commit()

    return RedirectResponse(url=f"/practice/{session.id}", status_code=303)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def health_db() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}

@router.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    current_user = get_current_user(request, db)

    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    stats = get_platform_stats(db)
    course_stats = get_course_enrollment_stats(db)
    lesson_stats = get_lesson_completion_stats(db)
    top_questions = get_top_coach_questions(db)
    lesson_struggles = get_lesson_struggle_stats(db)
    scenario_usage = get_scenario_usage_stats(db)

    return templates.TemplateResponse(
        "admin_analytics.html",
        {
            "request": request,
            "page_title": "Platform Analytics | MM",
            "current_user": current_user,
            "stats": stats,
            "course_stats": course_stats,
            "lesson_stats": lesson_stats,
            "top_questions": top_questions,
            "lesson_struggles": lesson_struggles,
            "scenario_usage": scenario_usage,
        },
    )