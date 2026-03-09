from dataclasses import dataclass


@dataclass
class AICoachResponse:
    answer: str
    guidance_type: str = "lesson_support"


def build_fallback_response(lesson_title: str, lesson_content: str, user_message: str) -> AICoachResponse:
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
"I’d like to finish my thought, please."
or
"Thanks — let me complete what I was saying."

Practice tip:
Try saying your response out loud once in a calm voice, then once with more confidence.

Lesson reminder:
{lesson_content}
""".strip()

    return AICoachResponse(answer=answer)


def get_lesson_coaching_response(
    lesson_title: str,
    lesson_content: str,
    user_message: str,
) -> AICoachResponse:
    # Temporary local fallback.
    # Later this will call the OpenAI API through a controlled service layer.
    return build_fallback_response(
        lesson_title=lesson_title,
        lesson_content=lesson_content,
        user_message=user_message,
    )