from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ParseRequest(BaseModel):
    message: str
    attachment_path: str | None = None


class StructuredFields(BaseModel):
    expense_type: str
    amount: str
    date_time: str
    from_to: str
    project: str
    cost_center: str
    summary: str
    summary_suggestion: str
    attachment_path: str


class PlanRequest(BaseModel):
    fields: StructuredFields


class ExecuteRequest(BaseModel):
    fields: StructuredFields


class ExecuteResult(BaseModel):
    expense_id: str
    status: str
    amount: str
    detail_url: str


class SessionInfo(BaseModel):
    session_id: str
    state: Literal[
        "idle",
        "executing",
        "awaiting_confirmation",
        "submitted",
        "failed",
    ]
    result: ExecuteResult | None = None
