from dataclasses import dataclass

from openai import OpenAI

from app.core.config import settings


@dataclass
class AICoachResponse:
    answer: str
    guidance_type: str = "lesson_support"
    used_fallback: bool = False


def build_fallback_response(
    lesson_title: str,
    lesson_content: str,
    user_message: str,
) -> AICoachResponse:
    answer = f"""
Lesson focus: {lesson_title}

You asked: {user_message}

Here is a respectful, practical approach:
1. Pause before reacting.
2. Speak clearly and calmly.
3. Use words that show respect for yourself and the other person.
4. Keep your tone steady and confident.
5. If needed, restate your point politely.

Example response:
"I'd like to finish my thought, please."
or
"Thanks — let me complete what I was saying."

Practice tip:
Try saying your response out loud once in a calm voice, then once with more confidence.

Lesson reminder:
{lesson_content}
""".strip()

    return AICoachResponse(
        answer=answer,
        guidance_type="lesson_support",
        used_fallback=True,
    )


def build_system_prompt() -> str:
    return """
You are the MM AI Coach for a modern manners and social skills LMS.

Your role:
- Help learners practice respectful communication.
- Be warm, practical, clear, and encouraging.
- Teach manners as practical respect, emotional intelligence, and self-confidence.
- Keep advice age-appropriate, non-shaming, and supportive.
- Do not provide unsafe, abusive, manipulative, sexual, or hateful guidance.
- Do not encourage humiliation, retaliation, cruelty, or deception.
- Prefer short examples, scripts, roleplay prompts, and step-by-step coaching.
- Stay grounded in the lesson topic and the learner's question.
- Do not claim professional legal, medical, or mental health authority.
- If a learner asks for something unsafe, redirect to a safer, respectful alternative.

Response style:
- Start with a direct answer.
- Then give 2-5 practical tips.
- Include 1 example phrase the learner can use.
- Keep the response concise and usable.
""".strip()


def get_lesson_coaching_response(
    lesson_title: str,
    lesson_content: str,
    user_message: str,
) -> AICoachResponse:
    if not settings.openai_api_key:
        return build_fallback_response(
            lesson_title=lesson_title,
            lesson_content=lesson_content,
            user_message=user_message,
        )

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        prompt = f"""
Lesson title: {lesson_title}

Lesson content:
{lesson_content}

Learner question:
{user_message}
""".strip()

        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": prompt},
            ],
        )

        answer = getattr(response, "output_text", "").strip()

        if not answer:
            return build_fallback_response(
                lesson_title=lesson_title,
                lesson_content=lesson_content,
                user_message=user_message,
            )

        return AICoachResponse(
            answer=answer,
            guidance_type="lesson_support",
            used_fallback=False,
        )

    except Exception:
        return build_fallback_response(
            lesson_title=lesson_title,
            lesson_content=lesson_content,
            user_message=user_message,
        )