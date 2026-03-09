from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.organization import Organization
from app.models.plan import Plan
from app.models.scenario import Scenario
from app.models.subscription import Subscription
from app.models.user import User


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # Organization
        org = db.query(Organization).filter(Organization.slug == "default-org").first()
        if not org:
            org = Organization(
                name="Default Organization",
                slug="default-org",
            )
            db.add(org)
            db.commit()
            db.refresh(org)

        # Admin user
        existing_user = db.query(User).filter(User.email == "admin@mm.local").first()
        if not existing_user:
            user = User(
                organization_id=org.id,
                full_name="Marlena Admin",
                email="admin@mm.local",
                hashed_password=hash_password("Password123!"),
                role="admin",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            existing_user = user
            print("Seed user created: admin@mm.local / Password123!")
        else:
            print("Seed user already exists: admin@mm.local / Password123!")

        # Courses and lessons
        courses_to_seed = [
            {
                "title": "Modern Manners Basics",
                "slug": "modern-manners-basics",
                "description": "Build a strong foundation in everyday respect, listening, courtesy, and self-awareness.",
                "difficulty": "beginner",
                "lessons": [
                    ("What Modern Manners Really Mean", "Modern manners are practical respect in action.", 1),
                    ("Respect at Home and School", "How to show consistent respect in daily life.", 2),
                    ("Listening with Intention", "Why active listening changes relationships.", 3),
                ],
            },
            {
                "title": "Digital Etiquette",
                "slug": "digital-etiquette",
                "description": "Learn how to communicate well online through messages, social media, and virtual spaces.",
                "difficulty": "beginner",
                "lessons": [
                    ("Thinking Before Posting", "Pause before posting or replying.", 1),
                    ("Texting with Clarity", "Clear communication avoids confusion.", 2),
                    ("Respect in Online Spaces", "Digital kindness still counts as real respect.", 3),
                ],
            },
            {
                "title": "Confident Communication",
                "slug": "confident-communication",
                "description": "Practice speaking clearly, handling interruptions, and building confidence in conversation.",
                "difficulty": "intermediate",
                "lessons": [
                    ("Strong Introductions", "How to introduce yourself with confidence.", 1),
                    ("Handling Awkward Moments", "Simple ways to respond with grace.", 2),
                    ("Speaking with Calm Confidence", "Confidence grows through preparation and presence.", 3),
                ],
            },
        ]

        for course_data in courses_to_seed:
            course = db.query(Course).filter(Course.slug == course_data["slug"]).first()
            if not course:
                course = Course(
                    organization_id=org.id,
                    title=course_data["title"],
                    slug=course_data["slug"],
                    description=course_data["description"],
                    difficulty=course_data["difficulty"],
                    published=True,
                )
                db.add(course)
                db.commit()
                db.refresh(course)

            for lesson_title, lesson_content, sort_order in course_data["lessons"]:
                lesson_slug = f"{course.slug}-lesson-{sort_order}"
                lesson = db.query(Lesson).filter(Lesson.slug == lesson_slug).first()
                if not lesson:
                    lesson = Lesson(
                        course_id=course.id,
                        title=lesson_title,
                        slug=lesson_slug,
                        content=lesson_content,
                        sort_order=sort_order,
                    )
                    db.add(lesson)

            db.commit()

        # Roleplay scenario
        intro_lesson = db.query(Lesson).filter(Lesson.slug == "modern-manners-basics-lesson-1").first()
        if intro_lesson:
            existing_scenario = db.query(Scenario).filter(Scenario.slug == "introduce-yourself-politely").first()
            if not existing_scenario:
                scenario = Scenario(
                    lesson_id=intro_lesson.id,
                    slug="introduce-yourself-politely",
                    title="Introduce Yourself Politely",
                    description="Practice introducing yourself respectfully and confidently to someone new.",
                    scenario_type="roleplay",
                    ai_role="Teacher",
                    learner_objective="Introduce yourself politely, clearly, and confidently.",
                    difficulty="beginner",
                    is_active=True,
                )
                db.add(scenario)
                db.commit()

        # Plans
        plans_to_seed = [
            {
                "name": "Free",
                "slug": "free",
                "description": "Starter access with limited AI coaching and practice.",
                "price_cents": 0,
                "billing_interval": "monthly",
                "max_ai_messages_per_month": 10,
                "max_practice_sessions_per_month": 3,
                "max_learners": 1,
                "includes_org_dashboard": False,
                "includes_advanced_analytics": False,
                "includes_roleplay": True,
            },
            {
                "name": "Premium",
                "slug": "premium",
                "description": "Full learner access with expanded AI coaching and practice.",
                "price_cents": 1900,
                "billing_interval": "monthly",
                "max_ai_messages_per_month": 200,
                "max_practice_sessions_per_month": 100,
                "max_learners": 1,
                "includes_org_dashboard": False,
                "includes_advanced_analytics": False,
                "includes_roleplay": True,
            },
            {
                "name": "Organization",
                "slug": "organization",
                "description": "For schools, nonprofits, and programs managing multiple learners.",
                "price_cents": 9900,
                "billing_interval": "monthly",
                "max_ai_messages_per_month": 5000,
                "max_practice_sessions_per_month": 1000,
                "max_learners": 250,
                "includes_org_dashboard": True,
                "includes_advanced_analytics": True,
                "includes_roleplay": True,
            },
        ]

        for plan_data in plans_to_seed:
            existing_plan = db.query(Plan).filter(Plan.slug == plan_data["slug"]).first()
            if not existing_plan:
                db.add(Plan(**plan_data))
                db.commit()

        # Assign free plan to admin
        free_plan = db.query(Plan).filter(Plan.slug == "free").first()
        if free_plan and existing_user:
            existing_subscription = (
                db.query(Subscription)
                .filter(
                    Subscription.user_id == existing_user.id,
                    Subscription.status == "active",
                )
                .first()
            )

            if not existing_subscription:
                subscription = Subscription(
                    user_id=existing_user.id,
                    plan_id=free_plan.id,
                    status="active",
                    provider="manual",
                )
                db.add(subscription)
                db.commit()

        print("Seed complete.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()