from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, ConversationSession
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


class MessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[MessageItem]
    session_id: Optional[str] = None
    stream: bool = True
    model: str = "deepseek-chat"


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
    ai: DeepSeekProvider = Depends(get_deepseek),
):
    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    # Save or update session
    session = None
    if body.session_id:
        result = await db.execute(
            select(ConversationSession).where(
                ConversationSession.id == body.session_id,
                ConversationSession.org_id == user.org_id,
            )
        )
        session = result.scalar_one_or_none()

    if not session:
        title = body.messages[0].content[:60] if body.messages else "New Chat"
        session = ConversationSession(
            org_id=user.org_id,
            user_id=user.id,
            title=title,
            messages=messages,
        )
        db.add(session)
        await db.flush()

    if body.stream:
        async def event_stream():
            full_response = ""
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session.id})}\n\n"
            async for chunk in await ai.chat(messages, model=body.model, stream=True):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            # Save assistant response
            session.messages = messages + [{"role": "assistant", "content": full_response}]

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    response = await ai.chat(messages, model=body.model, stream=False)
    session.messages = messages + [{"role": "assistant", "content": response}]
    return {"content": response, "session_id": session.id}


@router.get("/sessions")
async def list_sessions(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConversationSession)
        .where(ConversationSession.org_id == user.org_id)
        .order_by(ConversationSession.updated_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()
    return {
        "sessions": [
            {"id": s.id, "title": s.title, "created_at": str(s.created_at)}
            for s in sessions
        ],
        "total": len(sessions),
    }


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.org_id == user.org_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"messages": session.messages, "session_id": session.id, "title": session.title}
