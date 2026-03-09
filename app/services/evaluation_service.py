from dataclasses import dataclass

from openai import OpenAI

from app.core.config import settings


@dataclass
class EvaluationResult:
    score: int
    feedback_summary: str
    used_fallback: bool = False


def build_evaluation_system_prompt(
    scenario_title: str,
    ai_role: str,
    learner_objective: str,
) -> str:
    return f"""
You are evaluating a learner's performance in a social-skills roleplay for the MM learning platform.

Scenario:
{scenario_title}

AI role:
{ai_role}

Learner objective:
{learner_objective}

Evaluate the learner on:
- politeness
- clarity
- confidence
- emotional intelligence
- appropriateness to the scenario

Return feedback in exactly this format:

Score: X/10

Strengths:
- ...
- ...

Improvements:
- ...
- ...

Suggested Response:
...

Keep the feedback constructive, encouraging, specific, and age-appropriate.
""".strip()


def build_conversation_transcript(messages: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for msg in messages:
        speaker = "Learner" if msg["role"] == "user" else "Scenario Partner"
        lines.append(f"{speaker}: {msg['content']}")
    return "\n".join(lines)


def parse_score_from_text(feedback_summary: str) -> int:
    for line in feedback_summary.splitlines():
        line = line.strip()
        if line.lower().startswith("score:"):
            value = line.split(":", 1)[1].strip()
            if "/10" in value:
                value = value.split("/10", 1)[0].strip()
            try:
                score = int(value)
                return max(1, min(score, 10))
            except ValueError:
                pass
    return 7


def build_fallback_evaluation(
    scenario_title: str,
    learner_objective: str,
    messages: list[dict[str, str]],
) -> EvaluationResult:
    learner_turns = [m for m in messages if m["role"] == "user"]
    score = 8 if learner_turns else 6

    feedback_summary = f"""
Score: {score}/10

Strengths:
- You stayed engaged in the scenario.
- Your response supported the goal: {learner_objective}

Improvements:
- Add a little more warmth and confidence to your phrasing.
- Keep your response clear, respectful, and natural.

Suggested Response:
Hello, it’s nice to meet you. My name is Alex, and I’m glad to be here.

This feedback was generated using local fallback evaluation for the scenario "{scenario_title}".
""".strip()

    return EvaluationResult(
        score=score,
        feedback_summary=feedback_summary,
        used_fallback=True,
    )


def evaluate_roleplay_session(
    scenario_title: str,
    ai_role: str,
    learner_objective: str,
    messages: list[dict[str, str]],
) -> EvaluationResult:
    if not messages:
        return EvaluationResult(
            score=1,
            feedback_summary="""
Score: 1/10

Strengths:
- The session was started.

Improvements:
- Complete at least one learner response before evaluation.
- Try practicing again with a clear, respectful reply.

Suggested Response:
Hello, it’s nice to meet you. My name is Alex.
""".strip(),
            used_fallback=True,
        )

    if not settings.openai_api_key:
        return build_fallback_evaluation(
            scenario_title=scenario_title,
            learner_objective=learner_objective,
            messages=messages,
        )

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        transcript = build_conversation_transcript(messages)

        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": build_evaluation_system_prompt(
                        scenario_title=scenario_title,
                        ai_role=ai_role,
                        learner_objective=learner_objective,
                    ),
                },
                {
                    "role": "user",
                    "content": f"Evaluate this roleplay transcript:\n\n{transcript}",
                },
            ],
        )

        feedback_summary = getattr(response, "output_text", "").strip()

        if not feedback_summary:
            return build_fallback_evaluation(
                scenario_title=scenario_title,
                learner_objective=learner_objective,
                messages=messages,
            )

        score = parse_score_from_text(feedback_summary)

        return EvaluationResult(
            score=score,
            feedback_summary=feedback_summary,
            used_fallback=False,
        )

    except Exception:
        return build_fallback_evaluation(
            scenario_title=scenario_title,
            learner_objective=learner_objective,
            messages=messages,
        )