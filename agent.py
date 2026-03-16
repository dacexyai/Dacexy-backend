from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User, AiTask
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRunRequest(BaseModel):
    task: str
    context: Optional[str] = None
    max_steps: int = 10


@router.post("/run")
async def run_agent(
    body: AgentRunRequest,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
    ai: DeepSeekProvider = Depends(get_deepseek),
):
    system_prompt = """You are an autonomous AI agent for Dacexy Enterprise platform.
Break down tasks into steps and execute them systematically.
Think step by step and provide detailed responses."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Task: {body.task}" + (f"\nContext: {body.context}" if body.context else "")}
    ]

    task_record = AiTask(
        org_id=user.org_id,
        user_id=user.id,
        task_type="agent_run",
        status="running",
        input_data={"task": body.task, "context": body.context},
    )
    db.add(task_record)
    await db.flush()

    try:
        result = await ai.chat(messages, model="deepseek-chat", stream=False)
        task_record.status = "completed"
        task_record.output_data = {"result": result}
        return {"task_id": task_record.id, "status": "completed", "result": result}
    except Exception as e:
        task_record.status = "failed"
        task_record.error = str(e)
        raise HTTPException(500, f"Agent error: {str(e)}")


@router.get("/tasks")
async def list_tasks(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    result = await db.execute(
        select(AiTask)
        .where(AiTask.org_id == user.org_id)
        .order_by(AiTask.created_at.desc())
        .limit(20)
    )
    tasks = result.scalars().all()
    return {
        "tasks": [
            {"id": t.id, "task_type": t.task_type, "status": t.status,
             "created_at": str(t.created_at)}
            for t in tasks
        ]
    }
