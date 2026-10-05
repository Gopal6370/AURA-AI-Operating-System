from .memory_ai import extract_memories
from .context_engine import build_context
from .orchestrator import route_message
from pathlib import Path
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, routing
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .db import Base, engine, get_db
from .models import User, Conversation, Message, Memory, Task
from .schemas import RegisterIn, LoginIn, ChatIn, MemoryIn, TaskIn, TaskUpdate, DocumentQuery
from .security import hash_password, verify_password, create_token, current_user, bearer
from .ai import answer
from .rag import index_pdf, retrieve
from app import db
from .knowledge_graph import KnowledgeNode, KnowledgeEdge
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AURA API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def uid(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    return current_user(creds)

@app.get("/health")
def health():
    return {"status": "ok", "name": "AURA", "version": "1.0.0"}

@app.post("/api/auth/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(email=data.email, password_hash=hash_password(data.password), name=data.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id), "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"token": create_token(user.id), "user": {"id": user.id, "name": user.name, "email": user.email}}

@app.get("/api/me")
def me(user_id: int = Depends(uid), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    return {"id": user.id, "name": user.name, "email": user.email}

@app.get("/api/conversations")
def conversations(user_id: int = Depends(uid), db: Session = Depends(get_db)):
    rows = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(desc(Conversation.updated_at)).all()
    return [{"id": r.id, "title": r.title, "created_at": r.created_at.isoformat()} for r in rows]

@app.get("/api/conversations/{conversation_id}")
def conversation(conversation_id: int, user_id: int = Depends(uid), db: Session = Depends(get_db)):
    c = db.get(Conversation, conversation_id)
    if not c or c.user_id != user_id:
        raise HTTPException(404, "Conversation not found")
    rows = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.id).all()
    return [{"id": r.id, "role": r.role, "content": r.content, "agent": r.agent} for r in rows]

@app.post("/api/chat")
def chat(
    data: ChatIn,
    user_id: int = Depends(uid),
    db: Session = Depends(get_db)
):
    # -----------------------------------
    # 1. Find or create conversation
    # -----------------------------------

    if data.conversation_id:
        conv = db.get(Conversation, data.conversation_id)

        if not conv or conv.user_id != user_id:
            raise HTTPException(404, "Conversation not found")

    else:
        title = data.message[:60].strip()

        conv = Conversation(
            user_id=user_id,
            title=title or "New conversation"
        )

        db.add(conv)
        db.commit()
        db.refresh(conv)

    # -----------------------------------
    # 2. AURA ORCHESTRATOR
    # -----------------------------------

    routing = route_message(data.message)

    agent = routing.get("agent", "general")

    # -----------------------------------
    # 3. Previous conversation
    # -----------------------------------

    old = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(desc(Message.id))
        .limit(12)
        .all()
    )

    old = list(reversed(old))

    # -----------------------------------
    # 4. Save user message
    # -----------------------------------

    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=data.message,
        agent=agent
    )

    db.add(user_msg)
    db.commit()

    # -----------------------------------
    # 5. Get AURA memories
    # -----------------------------------

    memories = (
        db.query(Memory)
        .filter(Memory.user_id == user_id)
        .order_by(desc(Memory.id))
        .limit(10)
        .all()
    )

    memory_context = "\n".join(
        f"- {m.content}"
        for m in memories
    )

    # -----------------------------------
    # 6. Build conversation history
    # -----------------------------------

    history = [
        {
            "role": m.role,
            "content": m.content
        }
        for m in old
    ]

    history.append({
        "role": "user",
        "content": data.message
    })

    # -----------------------------------
    # 7. Research detection
    # -----------------------------------

    use_web = (
        agent == "research"
        or any(
            word in data.message.lower()
            for word in [
                "latest",
                "today",
                "current",
                "news",
                "recent",
                "price",
                "weather"
            ]
        )
    )

    # -----------------------------------
    # 8. Ask Gemini
    # -----------------------------------

    context = build_context(
    memories=memories,
    retrieved_documents=[],
    agent=agent
)
    try:
        result = answer(
            history,
            agent=agent,
            web_search=use_web,
            context=context
        )
    except Exception as exc:

        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}"
        )

    # -----------------------------------
    # 9. Save AURA response
    # -----------------------------------

    db.add(
        Message(
            conversation_id=conv.id,
            role="assistant",
            content=result,
            agent=agent
        )
    )

    db.commit()

    # ---------------------------------------------------------
    # AUTOMATIC MEMORY EXTRACTION
    # ---------------------------------------------------------

    try:
        conversation_text = "\n".join(
            f"{m.role}: {m.content}"
            for m in old
        )

        conversation_text += f"\nuser: {data.message}"
        conversation_text += f"\nassistant: {result}"

        extracted_memories = extract_memories(conversation_text)

        for memory_text in extracted_memories:
            # Avoid duplicate memories
            existing = (
                db.query(Memory)
                .filter(
                    Memory.user_id == user_id,
                    Memory.content == memory_text
                )
                .first()
            )

            if not existing:
                db.add(
                    Memory(
                        user_id=user_id,
                        content=memory_text
                    )
                )

        db.commit()

    except Exception as exc:
        print(
            "Automatic memory failed:",
            type(exc).__name__,
            str(exc)
        )

    # -----------------------------------
    # 10. Return automatic agent
    # -----------------------------------

    return {
        "conversation_id": conv.id,
        "answer": result,
        "agent": agent,
        "agent_name": routing.get(
            "agent_name",
            "General Agent"
        )
    }



    

@app.get("/api/memories")
def memories(user_id: int = Depends(uid), db: Session = Depends(get_db)):
    rows = db.query(Memory).filter(Memory.user_id == user_id).order_by(desc(Memory.id)).all()
    return [{"id": r.id, "content": r.content, "created_at": r.created_at.isoformat()} for r in rows]

@app.post("/api/memories")
def add_memory(data: MemoryIn, user_id: int = Depends(uid), db: Session = Depends(get_db)):
    row = Memory(user_id=user_id, content=data.content)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "content": row.content}

@app.delete("/api/memories/{memory_id}")
def delete_memory(memory_id: int, user_id: int = Depends(uid), db: Session = Depends(get_db)):
    row = db.get(Memory, memory_id)
    if not row or row.user_id != user_id:
        raise HTTPException(404, "Memory not found")
    db.delete(row)
    db.commit()
    return {"ok": True}

@app.get("/api/tasks")
def tasks(user_id: int = Depends(uid), db: Session = Depends(get_db)):
    rows = db.query(Task).filter(Task.user_id == user_id).order_by(desc(Task.id)).all()
    return [{
        "id": r.id, "title": r.title, "description": r.description,
        "due_date": r.due_date, "priority": r.priority, "status": r.status
    } for r in rows]

@app.post("/api/tasks")
def add_task(data: TaskIn, user_id: int = Depends(uid), db: Session = Depends(get_db)):
    row = Task(user_id=user_id, **data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, **data.model_dump(), "status": row.status}

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, data: TaskUpdate, user_id: int = Depends(uid), db: Session = Depends(get_db)):
    row = db.get(Task, task_id)
    if not row or row.user_id != user_id:
        raise HTTPException(404, "Task not found")
    row.status = data.status
    db.commit()
    return {"ok": True}

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, user_id: int = Depends(uid), db: Session = Depends(get_db)):
    row = db.get(Task, task_id)
    if not row or row.user_id != user_id:
        raise HTTPException(404, "Task not found")
    db.delete(row)
    db.commit()
    return {"ok": True}

@app.post("/api/documents/upload")
async def upload_pdf(file: UploadFile = File(...), user_id: int = Depends(uid), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    safe_name = Path(file.filename).name
    target = UPLOAD_DIR / f"{user_id}_{safe_name}"
    content = await file.read()
    target.write_bytes(content)
    try:
        count = index_pdf(db, user_id, str(target), safe_name)
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(400, f"PDF indexing failed: {exc}")
    return {"filename": safe_name, "chunks": count}

@app.post("/api/documents/query")
def query_document(data: DocumentQuery, user_id: int = Depends(uid), db: Session = Depends(get_db)):
    try:
        results = retrieve(db, user_id, data.query, data.top_k)
    except Exception as exc:
        raise HTTPException(500, str(exc))
    return [{
        "filename": f, "page": p, "text": t, "score": round(s, 4)
    } for f, p, t, s in results]

@app.get("/")
def index():
    return FileResponse("frontend/index.html")
