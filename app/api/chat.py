"""Chat API endpoints — session CRUD and SSE streaming messages."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, func, select

from app.db.database import async_session
from app.models.chat import ChatMessage, ChatSession
from app.services.chat_service import (
    build_chat_messages,
    retrieve_chat_context,
    stream_chat_completion,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── Schemas ───────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    title: str | None = None


class SessionSummary(BaseModel):
    id: int
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str


# ── Endpoints ─────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionSummary, status_code=201)
async def create_session(body: SessionCreate):
    """Create a new chat session."""
    async with async_session() as session:
        chat_session = ChatSession(title=body.title or "新对话")
        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)
        return SessionSummary(
            id=chat_session.id,
            title=chat_session.title,
            message_count=0,
            created_at=chat_session.created_at,
            updated_at=chat_session.updated_at,
        )


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(limit: int = 50, offset: int = 0):
    """List chat sessions with message count, newest first."""
    async with async_session() as session:
        msg_count = (
            select(
                ChatMessage.session_id,
                func.count(ChatMessage.id).label("message_count"),
            )
            .group_by(ChatMessage.session_id)
            .subquery()
        )

        result = await session.execute(
            select(
                ChatSession.id,
                ChatSession.title,
                ChatSession.created_at,
                ChatSession.updated_at,
                func.coalesce(msg_count.c.message_count, 0).label("message_count"),
            )
            .outerjoin(msg_count, ChatSession.id == msg_count.c.session_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return [
            SessionSummary(
                id=r.id,
                title=r.title,
                message_count=r.message_count,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in result.all()
        ]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: int):
    """Get a session with its message history."""
    async with async_session() as session:
        chat_session = await session.get(ChatSession, session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")

        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = result.scalars().all()

        return SessionDetail(
            id=chat_session.id,
            title=chat_session.title,
            created_at=chat_session.created_at,
            updated_at=chat_session.updated_at,
            messages=[
                MessageOut(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: int):
    """Delete a session and all its messages (CASCADE)."""
    async with async_session() as session:
        chat_session = await session.get(ChatSession, session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")
        await session.delete(chat_session)
        await session.commit()


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: int, body: SendMessageRequest):
    """Send a user message and stream the assistant reply via SSE."""
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    # Verify session exists
    async with async_session() as session:
        chat_session = await session.get(ChatSession, session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Save user message
        session.add(ChatMessage(
            session_id=session_id,
            role="user",
            content=content,
        ))

        # Auto-set title from first user message
        msg_count_result = await session.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session_id)
        )
        if msg_count_result.scalar() == 0:
            chat_session.title = content[:50]

        # Touch updated_at
        chat_session.updated_at = func.now()
        await session.commit()

    # RAG retrieval
    rag_context = await retrieve_chat_context(content)

    # Build messages for LLM
    messages = await build_chat_messages(session_id, content, rag_context)

    # Stream response as SSE
    async def event_stream():
        try:
            async for chunk in stream_chat_completion(messages, session_id):
                data = json.dumps({"content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception:
            logger.error("SSE stream error", exc_info=True)
            yield f"data: {json.dumps({'error': 'stream failed'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
