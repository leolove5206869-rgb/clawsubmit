from __future__ import annotations

import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright

from .schemas import ExecuteResult
from .session_manager import CHECKLIST, RECEIPT_STATUS, ExecutionSession


CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FIELD_DELAY_SECONDS = 0.18
SHORT_STEP_DELAY_SECONDS = 0.22
UPLOAD_DELAY_SECONDS = 0.28


async def highlight(page, selector: str) -> None:
    await page.locator(selector).evaluate(
        """
        (element) => {
          document.querySelectorAll('[data-claw-highlighted="true"]').forEach((node) => {
            node.removeAttribute('data-claw-highlighted');
          });
          element.setAttribute('data-claw-highlighted', 'true');
          element.scrollIntoView({ block: 'center', behavior: 'instant' });
        }
        """
    )


async def fill_field(page, selector: str, value: str, session: ExecutionSession, label: str) -> None:
    await highlight(page, selector)
    await session.log(f"填写 {label}: {value}")
    await page.locator(selector).fill(value)
    await asyncio.sleep(FIELD_DELAY_SECONDS)


async def run_automation(session: ExecutionSession, base_url: str, samples_dir: Path) -> None:
    browser = None
    try:
        async with async_playwright() as playwright:
            launch_kwargs = {"headless": True}
            if os.path.exists(CHROME_PATH):
                launch_kwargs["executable_path"] = CHROME_PATH

            browser = await playwright.chromium.launch(**launch_kwargs)
            page = await browser.new_page()

            await session.set_state("executing")
            await session.log("启动本地沙盒报销系统")
            await page.goto(f"{base_url}/expense/new", wait_until="networkidle")
            await session.advance_step(0)
            await asyncio.sleep(SHORT_STEP_DELAY_SECONDS)

            await session.advance_step(1)
            await fill_field(page, '[data-testid="expense-type"]', session.fields.expense_type, session, "费用类型")

            await session.advance_step(2)
            await fill_field(page, '[data-testid="amount"]', session.fields.amount, session, "金额")
            await fill_field(page, '[data-testid="date-time"]', session.fields.date_time, session, "时间")
            await fill_field(page, '[data-testid="from-to"]', session.fields.from_to, session, "出发地/目的地")
            await fill_field(page, '[data-testid="project"]', session.fields.project, session, "项目")
            await fill_field(page, '[data-testid="cost-center"]', session.fields.cost_center, session, "成本中心")
            await fill_field(page, '[data-testid="summary"]', session.fields.summary, session, "摘要")

            await session.advance_step(3)
            attachment_name = Path(session.fields.attachment_path).name
            upload_path = samples_dir / attachment_name
            await highlight(page, '[data-testid="attachment"]')
            await session.log(f"上传附件: {upload_path.name}")
            await page.locator('[data-testid="attachment"]').set_input_files(str(upload_path))
            await asyncio.sleep(UPLOAD_DELAY_SECONDS)

            await session.advance_step(4)
            await session.set_state("awaiting_confirmation")
            await session.emit(
                "confirmation_requested",
                {
                    "session_id": session.session_id,
                    "message": f"即将提交报销单：金额 {session.fields.amount}，成本中心 {session.fields.cost_center}，项目 {session.fields.project}。确认提交？",
                },
            )
            await session.log("已暂停，等待人工确认后提交")
            await session.confirm_event.wait()

            await session.advance_step(5)
            await session.set_state("executing")
            await session.log("收到确认，提交报销单")
            await highlight(page, '[data-testid="submit-expense"]')
            await page.locator('[data-testid="submit-expense"]').click()
            await page.wait_for_url(f"{base_url}/expense/**", wait_until="networkidle")
            receipt_id = await page.locator('[data-testid="receipt-id"]').inner_text()
            status = await page.locator('[data-testid="receipt-status"]').inner_text()
            amount = await page.locator('[data-testid="receipt-amount"]').inner_text()

            await session.advance_step(6)
            await session.log(f"读取回执单号: {receipt_id}")
            await session.log(f"已回写本地聊天面板: {receipt_id}")

            result = ExecuteResult(
                expense_id=receipt_id,
                status=status,
                amount=amount.replace("¥", ""),
                detail_url=f"/expense/{receipt_id}",
            )
            await session.set_state("submitted")
            await session.complete(result)
    except Exception as exc:  # pragma: no cover - exercised in integration path
        await session.fail(str(exc))
    finally:
        if browser:
            await browser.close()
