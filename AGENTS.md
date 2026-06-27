# Law Agent Maintenance Guide

## Project State

- Repository: `ava-agent/law-agent`
- Public URL: `https://law.rxcloud.group`
- Stack: FastAPI, Jinja/static frontend, Volcengine Ark/OpenAI-compatible client, python-docx, Supabase
- Product: consumer-rights legal consultation, complaint workflow, and document generation assistant.

## Before Editing

- Treat generated legal advice and documents as user-facing high-risk output; keep disclaimers and source law references clear.
- Keep Ark and Supabase credentials in local `.env` or deployment secrets.
- Do not commit generated documents under `static/generated/` or filled environment files.

## Useful Commands

- Install: `pip install -r requirements.txt`
- Run locally: `python main.py`
- Docker compose: `docker compose up --build`
- Vercel entry point: `api/index.py`

## Deployment Notes

- Vercel config is present in `vercel.json`; Docker and Compose paths also exist.
- Public domain should stay aligned with `https://law.rxcloud.group`.
- Validate chat streaming, platform recommendation, document generation, and Supabase upload after deployment changes.
