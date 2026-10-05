# AURA — Autonomous Universal Reasoning Assistant

An AI Operating System that thinks, learns, remembers, collaborates, and acts.

## What this version includes

AURA v1 is deliberately designed for a laptop **without a GPU**.

- FastAPI backend
- Browser-based dashboard
- SQLite database (no PostgreSQL required for v1)
- JWT login/register
- AI chat using the OpenAI Responses API
- Agent router: General / Study / Coding / Research / Career / Productivity
- Web research mode using the Responses API web-search tool
- PDF upload + local chunking + OpenAI embeddings + cosine retrieval
- Persistent memories
- Conversation history
- Simple task planner
- Browser voice input/output when supported
- No local LLM or GPU required

The AI computation is performed by the API provider; your laptop mainly runs the web server, database, PDF parsing, and retrieval.

## Requirements

- Windows 11
- Python 3.11+ recommended
- Internet connection
- An OpenAI API key
- VS Code

## 1. Open the project

Extract the ZIP and open the `AURA` folder in VS Code.

## 2. Create a virtual environment

PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Install packages

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Configure the API key

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.6
EMBEDDING_MODEL=text-embedding-3-small
```

Keep `.env` private. Never upload it to GitHub.

## 5. Start AURA

```powershell
python -m uvicorn app.main:app --reload
```

Open:

http://127.0.0.1:8000

API health check:

http://127.0.0.1:8000/health

## 6. First use

1. Register an account.
2. Log in.
3. Open Chat.
4. Select an agent.
5. Ask a question.
6. Try Research for current information.
7. Upload a PDF in Knowledge.
8. Ask questions about the uploaded PDF.
9. Add a memory such as "I prefer concise explanations."
10. Add tasks in Planner.

## Architecture

```text
Browser
   |
   v
FastAPI
   |
   +---- Authentication ---- SQLite
   |
   +---- Chat ------------- OpenAI Responses API
   |
   +---- Research --------- OpenAI web_search tool
   |
   +---- Knowledge -------- PDF -> chunks -> embeddings -> cosine search
   |
   +---- Memory ----------- SQLite
   |
   +---- Planner --------- SQLite
```

## Important GPU note

Do NOT install CUDA, PyTorch, Ollama, or a local LLM just to run this version.

AURA v1 uses cloud AI APIs, so a CPU-only laptop is sufficient.

## Future AURA versions

After v1 is stable, add:

- PostgreSQL
- Redis
- background workers
- streaming responses
- better vector database
- OAuth
- GitHub integration
- Gmail/Calendar integration
- Notion integration
- safe code execution sandbox
- computer-use tools
- desktop app
- mobile app
- local LLM fallback
- multi-agent orchestration
- notification service
- project/workspace system
- advanced memory graph
