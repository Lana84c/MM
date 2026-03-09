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
    learner_context: str | None = None,
) -> AICoachResponse:
    context_block = f"\nLearner context:\n{learner_context}\n" if learner_context else ""

    answer = f"""
Lesson focus: {lesson_title}
{context_block}
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
- Stay grounded in the lesson topic, learner history, and current question.
- Use learner progress context when helpful.
- Do not claim professional legal, medical, or mental health authority.
- If a learner asks for something unsafe, redirect to a safer, respectful alternative.

Response style:
- Start with a direct answer.
- Then give 2-5 practical tips.
- Include 1 example phrase the learner can use.
- Keep the response concise and usable.
""".strip()


def build_history_messages(history) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []

    if not history:
        return messages

    for msg in history:
        messages.append(
            {
                "role": msg.role,
                "content": msg.content,
            }
        )

    return messages


def get_lesson_coaching_response(
    lesson_title: str,
    lesson_content: str,
    user_message: str,
    history=None,
    learner_context: str | None = None,
) -> AICoachResponse:
    if not settings.openai_api_key:
        return build_fallback_response(
            lesson_title=lesson_title,
            lesson_content=lesson_content,
            user_message=user_message,
            learner_context=learner_context,
        )

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        prompt_parts = [
            f"Lesson title: {lesson_title}",
            f"Lesson content:\n{lesson_content}",
        ]

        if learner_context:
            prompt_parts.append(f"Learner context:\n{learner_context}")

        prompt_parts.append(f"Learner question:\n{user_message}")
        prompt = "\n\n".join(prompt_parts)

        messages = [
            {"role": "system", "content": build_system_prompt()},
        ]

        messages += build_history_messages(history)
        messages.append({"role": "user", "content": prompt})

        response = client.responses.create(
            model=settings.openai_model,
            input=messages,
        )

        answer = getattr(response, "output_text", "").strip()

        if not answer:
            return build_fallback_response(
                lesson_title=lesson_title,
                lesson_content=lesson_content,
                user_message=user_message,
                learner_context=learner_context,
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
            learner_context=learner_context,
        )