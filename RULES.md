# VibeCheck: Multimodal Virality Engine - Project Rules

1. Work only inside this workspace (`C:\Users\somti\Downloads\VibeCheck`). Do not touch anything outside it.
2. Do ONLY the part requested. When done, STOP and reply in this format:
   `"Part X done. Progress: Y%. Files created: ... Commands run: ... Test results: ... Problems: ... Ready for 'continue'?"`
3. Keep code simple and beginner-readable. Every file starts with a short plain-English comment saying what it is for. No clever tricks, no extra libraries.
4. Never add features, endpoints, tables or columns that are not in instructions. Never remove any that are.
5. No real secrets in the project. Use `.env.example` with placeholders; real values go in a `.env` that is listed in `.gitignore`.
6. Never say "tested" or "works" unless actually run and seen to pass. Show the real output. If something fails twice, stop and show the exact error.
7. Real AI models (Whisper, OpenCV, CLIP, LLMs) are OUT of scope. Use mock functions that return fake but realistic data, each marked with the comment `"MOCK - replace with real model"`.
8. Tech stack is fixed: Python + FastAPI, PostgreSQL 15, Celery + Redis, minimal Next.js, Docker Compose. Do not change it.
9. Save these rules to `RULES.md` in the workspace root.
10. At the end of every part, print the workspace path again and list the top-level folders to confirm files are in the workspace.

