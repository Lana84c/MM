from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Course, Enrollment, Lesson, Organization, Progress, User


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    org = db.query(Organization).filter(Organization.slug == "default-org").first()
    if not org:
        org = Organization(name="Default Organization", slug="default-org")
        db.add(org)
        db.commit()
        db.refresh(org)

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
        print("Seed user created: admin@mm.local / Password123!")
    else:
        print("Seed user already exists: admin@mm.local / Password123!")

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

    print("Sample courses and lessons seeded.")
    db.close()


if __name__ == "__main__":
    seed()