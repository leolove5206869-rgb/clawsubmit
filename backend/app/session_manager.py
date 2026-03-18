from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from .schemas import ExecuteResult, StructuredFields


RECEIPT_ID = "BX-20260318-0042"
RECEIPT_STATUS = "待审批"
CHECKLIST = [
    "打开报销系统并进入新建报销单",
    "选择费用类型：差旅-打车",
    "填写金额、时间、出发地/目的地、项目、成本中心、摘要",
    "上传发票附件",
    "提交前请求人工确认",
    "提交报销单并获取单号",
    "回写回执消息到本地聊天面板",
]


@dataclass
class ExecutionSession:
    fields: StructuredFields
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)
    confirm_event: asyncio.Event = field(default_factory=asyncio.Event)
    done_event: asyncio.Event = field(default_factory=asyncio.Event)
    state: str = "executing"
    current_step: int = -1
    result: ExecuteResult | None = None
    error: str | None = None

    async def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        message = f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
        await self.queue.put(message)

    async def set_state(self, state: str) -> None:
        self.state = state
        await self.emit("state", {"state": state, "session_id": self.session_id})

    async def log(self, message: str) -> None:
        await self.emit("log", {"message": message, "session_id": self.session_id})

    async def advance_step(self, step_index: int) -> None:
        self.current_step = step_index
        await self.emit(
            "step",
            {
                "session_id": self.session_id,
                "step_index": step_index,
                "step_label": CHECKLIST[step_index],
            },
        )

    async def complete(self, result: ExecuteResult) -> None:
        self.result = result
        await self.emit("completed", result.model_dump())
        self.done_event.set()

    async def fail(self, error: str) -> None:
        self.error = error
        self.state = "failed"
        await self.emit("failed", {"error": error, "session_id": self.session_id})
        self.done_event.set()


class SessionManager:
    def __init__(self) -> None:
        self.sessions: dict[str, ExecutionSession] = {}
        self.active_session_id: str | None = None
        self._lock = asyncio.Lock()

    async def create_session(self, fields: StructuredFields) -> ExecutionSession:
        async with self._lock:
            if self.active_session_id:
                active = self.sessions.get(self.active_session_id)
                if active and active.state in {"executing", "awaiting_confirmation"}:
                    raise RuntimeError("Another demo run is already active.")

            session = ExecutionSession(fields=fields)
            self.sessions[session.session_id] = session
            self.active_session_id = session.session_id
            return session

    def get_session(self, session_id: str) -> ExecutionSession | None:
        return self.sessions.get(session_id)

    async def release_active(self, session_id: str) -> None:
        async with self._lock:
            if self.active_session_id == session_id:
                self.active_session_id = None
