from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .automation import run_automation
from .schemas import ExecuteRequest, ParseRequest, PlanRequest, SessionInfo, StructuredFields
from .session_manager import CHECKLIST, RECEIPT_ID, RECEIPT_STATUS, SessionManager


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
SAMPLES_DIR = PROJECT_DIR / "samples"
SAMPLE_MESSAGE = "“@行政 麻烦报销一下：昨晚 21:30 从虹桥到公司打车 86.50，项目：龙虾黑客松，成本中心：市场部。发票见图。”"
FIXED_FIELDS = StructuredFields(
    expense_type="差旅-打车",
    amount="86.50",
    date_time="2026-03-18 21:30",
    from_to="虹桥 -> 公司",
    project="龙虾黑客松",
    cost_center="市场部",
    summary="",
    summary_suggestion="龙虾黑客松差旅打车",
    attachment_path="/samples/invoice.jpg",
)

app = FastAPI(title="ClawSubmit Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = SessionManager()

if SAMPLES_DIR.exists():
    app.mount("/samples", StaticFiles(directory=SAMPLES_DIR), name="samples")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sample")
async def sample() -> dict[str, str]:
    return {
        "message": SAMPLE_MESSAGE,
        "attachment_path": "/samples/invoice.jpg",
    }


@app.post("/parse")
async def parse(_: ParseRequest) -> dict[str, str]:
    return FIXED_FIELDS.model_dump()


@app.post("/plan")
async def plan(_: PlanRequest) -> dict[str, list[str]]:
    return {"checklist": CHECKLIST}


@app.post("/execute")
async def execute(request: ExecuteRequest) -> dict[str, str]:
    try:
        session = await manager.create_session(request.fields)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    async def delayed_start() -> None:
        await asyncio.sleep(0.3)
        await run_automation(session, "http://127.0.0.1:8000", SAMPLES_DIR)

    asyncio.create_task(delayed_start())
    return {"session_id": session.session_id, "state": session.state}


@app.post("/execute/{session_id}/confirm")
async def confirm_execution(session_id: str) -> dict[str, str]:
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.state != "awaiting_confirmation":
        raise HTTPException(status_code=409, detail="Session is not waiting for confirmation")

    session.confirm_event.set()
    await session.log("前端已确认提交")
    return {"session_id": session_id, "state": "resuming"}


@app.get("/execute/{session_id}", response_model=SessionInfo)
async def get_execution(session_id: str) -> SessionInfo:
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfo(session_id=session_id, state=session.state, result=session.result)


@app.get("/events/{session_id}")
async def stream(session_id: str) -> StreamingResponse:
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        yield "event: ready\ndata: {\"ok\": true}\n\n"
        while True:
            if session.done_event.is_set() and session.queue.empty():
                break
            try:
                message = await asyncio.wait_for(session.queue.get(), timeout=15)
                yield message
            except asyncio.TimeoutError:
                yield "event: ping\ndata: {}\n\n"

        await manager.release_active(session_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/expense/new", response_class=HTMLResponse)
async def expense_new() -> HTMLResponse:
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>ClawSubmit Sandbox Expense</title>
            <style>
              :root {{
                color-scheme: dark;
                --bg: #0b1220;
                --panel: #131c2e;
                --panel-border: #27324a;
                --text: #eef2ff;
                --muted: #8ea0c7;
                --accent: #5eead4;
                --accent-2: #fbbf24;
                --danger: #f87171;
              }}
              body {{
                margin: 0;
                min-height: 100vh;
                font-family: "SF Pro Display", "PingFang SC", sans-serif;
                background: radial-gradient(circle at top, #14213d, var(--bg) 60%);
                color: var(--text);
                display: flex;
                justify-content: center;
                align-items: flex-start;
                padding: 32px;
              }}
              .shell {{
                width: min(760px, 100%);
                background: rgba(19, 28, 46, 0.94);
                border: 1px solid var(--panel-border);
                border-radius: 24px;
                padding: 28px;
                box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
              }}
              h1 {{
                margin: 0 0 8px;
                font-size: 28px;
              }}
              p {{
                margin: 0 0 20px;
                color: var(--muted);
              }}
              form {{
                display: grid;
                gap: 16px;
              }}
              label {{
                display: grid;
                gap: 8px;
                font-size: 14px;
                color: var(--muted);
              }}
              input {{
                background: rgba(11, 18, 32, 0.8);
                border: 1px solid var(--panel-border);
                border-radius: 14px;
                padding: 14px;
                color: var(--text);
                font-size: 16px;
                outline: none;
                transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
              }}
              input:focus {{
                border-color: var(--accent);
                box-shadow: 0 0 0 3px rgba(94, 234, 212, 0.12);
              }}
              [data-claw-highlighted="true"] {{
                border-color: var(--accent-2) !important;
                box-shadow: 0 0 0 4px rgba(251, 191, 36, 0.18) !important;
                transform: translateY(-1px);
              }}
              .footer {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 12px;
              }}
              .status {{
                font-size: 13px;
                color: var(--muted);
              }}
              button {{
                border: 0;
                border-radius: 999px;
                padding: 14px 20px;
                font-size: 15px;
                font-weight: 700;
                background: linear-gradient(135deg, var(--accent), #38bdf8);
                color: #06111e;
                cursor: pointer;
              }}
            </style>
          </head>
          <body>
            <div class="shell">
              <h1>本地报销沙盒系统</h1>
              <p>受控环境，仅供 ClawSubmit 自动化演示使用。</p>
              <form action="/expense/submit" method="post" enctype="multipart/form-data">
                <label>费用类型
                  <input data-testid="expense-type" name="expense_type" />
                </label>
                <label>金额
                  <input data-testid="amount" name="amount" />
                </label>
                <label>时间
                  <input data-testid="date-time" name="date_time" />
                </label>
                <label>出发地/目的地
                  <input data-testid="from-to" name="from_to" />
                </label>
                <label>项目
                  <input data-testid="project" name="project" />
                </label>
                <label>成本中心
                  <input data-testid="cost-center" name="cost_center" />
                </label>
                <label>报销摘要
                  <input data-testid="summary" name="summary" />
                </label>
                <label>附件上传
                  <input data-testid="attachment" type="file" name="attachment" accept=".jpg,.jpeg,.png" />
                </label>
                <div class="footer">
                  <div class="status">提交流程将生成固定单号 {RECEIPT_ID}</div>
                  <button data-testid="submit-expense" type="submit">提交报销单</button>
                </div>
              </form>
            </div>
          </body>
        </html>
        """
    )


@app.post("/expense/submit")
async def submit_expense(
    expense_type: str = Form(...),
    amount: str = Form(...),
    date_time: str = Form(...),
    from_to: str = Form(...),
    project: str = Form(...),
    cost_center: str = Form(...),
    summary: str = Form(...),
    attachment: UploadFile = File(...),
) -> RedirectResponse:
    _ = (expense_type, date_time, from_to, project, cost_center, summary, attachment.filename)
    return RedirectResponse(url=f"/expense/{RECEIPT_ID}?amount={amount}", status_code=303)


@app.get("/expense/{expense_id}", response_class=HTMLResponse)
async def expense_detail(expense_id: str, amount: str = "86.50") -> HTMLResponse:
    submitted_at = datetime(2026, 3, 18, 21, 31).strftime("%Y-%m-%d %H:%M")
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Expense Detail</title>
            <style>
              body {{
                margin: 0;
                min-height: 100vh;
                display: grid;
                place-items: center;
                background: linear-gradient(180deg, #07111f 0%, #081522 100%);
                color: #f8fafc;
                font-family: "SF Pro Display", "PingFang SC", sans-serif;
              }}
              .card {{
                width: min(560px, calc(100vw - 48px));
                padding: 28px;
                border-radius: 24px;
                background: rgba(10, 20, 35, 0.94);
                border: 1px solid rgba(94, 234, 212, 0.2);
                box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
              }}
              .badge {{
                display: inline-flex;
                padding: 6px 12px;
                border-radius: 999px;
                background: rgba(34, 197, 94, 0.18);
                color: #86efac;
                font-weight: 700;
              }}
              dl {{
                margin: 20px 0 0;
                display: grid;
                gap: 14px;
              }}
              dt {{
                font-size: 13px;
                color: #94a3b8;
              }}
              dd {{
                margin: 6px 0 0;
                font-size: 22px;
                font-weight: 700;
              }}
            </style>
          </head>
          <body>
            <div class="card">
              <div class="badge">提交成功</div>
              <dl>
                <div>
                  <dt>报销单号</dt>
                  <dd data-testid="receipt-id">{expense_id}</dd>
                </div>
                <div>
                  <dt>状态</dt>
                  <dd data-testid="receipt-status">{RECEIPT_STATUS}</dd>
                </div>
                <div>
                  <dt>金额</dt>
                  <dd data-testid="receipt-amount">¥{amount}</dd>
                </div>
                <div>
                  <dt>提交时间</dt>
                  <dd data-testid="receipt-time">{submitted_at}</dd>
                </div>
              </dl>
            </div>
          </body>
        </html>
        """
    )
