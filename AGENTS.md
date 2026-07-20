# AGENTS.md

## Project Overview

Dify is an open-source platform for developing LLM applications with an intuitive interface combining agentic AI workflows, RAG pipelines, agent capabilities, and model management.

The codebase is split into:

- **Backend API** (`/api`): Python Flask application organized with Domain-Driven Design
- **Frontend Web** (`/web`): Next.js application using TypeScript and React
- **Docker deployment** (`/docker`): Containerized deployment configurations
- **Dify Agent Backend** (`/dify-agent`): Backend services for managing and executing agent

## Backend Workflow

- Read `api/AGENTS.md` for details
- Run backend CLI commands through `uv run --project api <command>`.
- Integration tests are CI-only and are not expected to run in the local environment.

## Frontend Workflow

- Read `web/AGENTS.md` for details

## Testing & Quality Practices

- Follow TDD: red → green → refactor.
- Use `pytest` for backend tests with Arrange-Act-Assert structure.
- Enforce strong typing; avoid `Any` and prefer explicit type annotations.
- Write self-documenting code; only add comments that explain intent.

## Language Style

- **Python**: Keep type hints on functions and attributes, and implement relevant special methods (e.g., `__repr__`, `__str__`). Prefer `TypedDict` over `dict` or `Mapping` for type safety and better code documentation.
- **TypeScript**: Use the strict config, rely on ESLint (`pnpm lint:fix` preferred) plus `pnpm type-check`, and avoid `any` types.

## General Practices

- Prefer editing existing files; add new documentation only when requested.
- Inject dependencies through constructors and preserve clean architecture boundaries.
- Handle errors with domain-specific exceptions at the correct layer.

## Blog Writing Handoff

When writing public-facing RuyiDify blogs:

- Write finished posts under `docs\博客\` in this repository. Do not split blog posts by year or month.
- Treat `docs\博客\001_我重新看了一遍Dify，决定把RuyiDify做成一门实战课.md` as the current reference sample.
- Write from Zhang Dapeng's first-person perspective as a real expert project story.
- Blogs are plain-text by default. Do not insert images unless the user explicitly asks for an illustrated post.
- Use Markdown lists when they improve scanning. Every public blog list item should start with a suitable, meaningful emoji.
- Avoid meaningless repeated emoji and decorative double bullets such as `- 🟣 ...`.
- Do not expose local absolute paths in published article bodies. Use GitHub/network URLs, public repository names, or reader-facing descriptions instead.
- Do not commit, push, create pull requests, or publish writing changes unless the user explicitly asks for that action in the current task.

## Project Conventions

- Backend architecture adheres to DDD and Clean Architecture principles.
- Async work runs through Celery with Redis as the broker.
- Frontend user-facing strings must use `web/i18n/en-US/`; avoid hardcoded text.
