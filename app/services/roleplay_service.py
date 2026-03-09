from dataclasses import dataclass

from openai import OpenAI

from app.core.config import settings


@dataclass
class RoleplayResponse:
    answer: str
    used_fallback: bool = False


def build_roleplay_system_prompt(ai_role: str, learner_objective: str) -> str:
    return f"""
You are running a live social-skills roleplay inside the MM learning platform.

Your role in the scenario:
{ai_role}

Learner objective:
{learner_objective}

Instructions:
- Stay in character.
- Keep responses short and natural.
- Give the learner room to respond.
- Focus on respectful communication, confidence, and emotional intelligence.
- Do not over-explain unless the learner asks for help.
- If the learner struggles, gently coach them and continue the scenario.
- Keep the roleplay realistic, supportive, and age-appropriate.
""".strip()


def build_roleplay_fallback(
    scenario_title: str,
    ai_role: str,
    learner_objective: str,
) -> RoleplayResponse:
    answer = f"""
Scenario: {scenario_title}

I am roleplaying as: {ai_role}

Your goal:
{learner_objective}

Let's begin.

Hello there — I don’t think we’ve met yet. Would you like to introduce yourself?
""".strip()

    return RoleplayResponse(answer=answer, used_fallback=True)


def get_roleplay_opening_response(
    scenario_title: str,
    ai_role: str,
    learner_objective: str,
) -> RoleplayResponse:
    if not settings.openai_api_key:
        return build_roleplay_fallback(
            scenario_title=scenario_title,
            ai_role=ai_role,
            learner_objective=learner_objective,
        )

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": build_roleplay_system_prompt(ai_role, learner_objective),
                },
                {
                    "role": "user",
                    "content": f"Start the roleplay for this scenario: {scenario_title}",
                },
            ],
        )

        answer = getattr(response, "output_text", "").strip()

        if not answer:
            return build_roleplay_fallback(
                scenario_title=scenario_title,
                ai_role=ai_role,
                learner_objective=learner_objective,
            )

        return RoleplayResponse(answer=answer, used_fallback=False)

    except Exception:
        return build_roleplay_fallback(
            scenario_title=scenario_title,
            ai_role=ai_role,
            learner_objective=learner_objective,
        )


def get_roleplay_turn_response(
    scenario_title: str,
    ai_role: str,
    learner_objective: str,
    history: list[dict[str, str]],
    user_message: str,
) -> RoleplayResponse:
    if not settings.openai_api_key:
        answer = f"""
Thanks for your response.

Stay calm, clear, and respectful.

Now I’ll continue the scenario as {ai_role}:

That was a good start. Tell me a little more about yourself.
""".strip()
        return RoleplayResponse(answer=answer, used_fallback=True)

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        messages = [
            {
                "role": "system",
                "content": build_roleplay_system_prompt(ai_role, learner_objective),
            },
            {
                "role": "user",
                "content": f"Scenario title: {scenario_title}",
            },
        ]

        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        response = client.responses.create(
            model=settings.openai_model,
            input=messages,
        )

        answer = getattr(response, "output_text", "").strip()

        if not answer:
            answer = f"""
That was a solid effort. Let’s continue.

As {ai_role}, I’d respond:
Nice to meet you. What brings you here today?
""".strip()
            return RoleplayResponse(answer=answer, used_fallback=True)

        return RoleplayResponse(answer=answer, used_fallback=False)

    except Exception:
        answer = f"""
That was a solid effort. Let’s continue.

As {ai_role}, I’d respond:
Nice to meet you. What brings you here today?
""".strip()
        return RoleplayResponse(answer=answer, used_fallback=True)