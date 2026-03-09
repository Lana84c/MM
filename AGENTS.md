\# AGENTS.md



\## Project Overview

This project is a Python-first SaaS LMS with an AI Coach for teaching modern manners and social skills.



The system is multi-tenant (organization scoped) and designed to support learners, parents, instructors, and administrators.



\## Core Stack

Backend: FastAPI  

Templates: Jinja2  

Frontend interactivity: HTMX  

Database: PostgreSQL  

ORM: SQLAlchemy  

Auth: secure cookie sessions or JWT  

Storage: S3-compatible storage  

Optional queue: Redis + RQ or Celery  

AI: OpenAI API behind a single AI Coach service



Keep the application Python-first and avoid unnecessary frontend frameworks.



\## Architecture Principles

\- Maintain strict tenant isolation between organizations.

\- Keep the codebase modular and service-oriented.

\- Prefer server-rendered UI over heavy client-side JavaScript.

\- Build reusable services for authentication, courses, progress tracking, and AI interaction.



\## Code Standards

\- Follow Python best practices (PEP8).

\- Use clear naming and modular functions.

\- Prefer readability over clever code.

\- Include type hints where useful.

\- Avoid unnecessary complexity.



\## Dependency Policy

\- Avoid adding new dependencies unless necessary.

\- Prefer Python standard library when possible.

\- Reuse existing project utilities.



\## Security

\- Never expose API keys or credentials.

\- Validate all inputs.

\- Protect tenant data boundaries.

\- Use secure password hashing (bcrypt).



\## Testing

\- Run tests and linters for functional code changes.

\- Do NOT run tests when only comments, documentation, or formatting change.

\- Add tests for new logic where appropriate.



\## AI Coach Rules

\- AI responses must be supportive, constructive, and respectful.

\- No shaming language.

\- Content should align with emotional intelligence and respectful communication.



\## Output Expectations

\- Make minimal, targeted code changes.

\- Explain non-obvious design decisions briefly.

\- Keep commits and pull requests clean and professional.

