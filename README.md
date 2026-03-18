# ClawSubmit

**ClawSubmit is an execution-native AI agent demo that turns chat input into a real submitted expense workflow.**

It does not stop at summarizing or extracting fields. It takes an unstructured message plus an invoice image, generates structured expense data, creates an execution plan, fills a real local sandbox expense system, pauses for human confirmation, submits the form, and writes the receipt back into the chat panel.

## Why This Exists

Most AI assistants stop at:

- summarizing a request
- extracting fields
- generating a draft
- telling the user what to do next

ClawSubmit demonstrates the next step:

**the agent actually completes the workflow.**

This repo is built as a hackathon-ready, local-first demo of an execution-native productivity agent.

## Demo Flow

ClawSubmit shows one complete, deterministic workflow:

1. User enters a natural-language reimbursement message plus an invoice image
2. The app returns fixed structured expense fields
3. The app returns a fixed execution checklist
4. Playwright fills a real local expense form step by step
5. The agent pauses before submission for human confirmation
6. The expense is submitted into the sandbox system
7. A fixed receipt ID is returned: `BX-20260318-0042`
8. A write-back confirmation appears in the local chat panel

Core message:

> **We do not just summarize tasks. We actually submit them.**

## What The Demo Shows

- Unstructured task intake through a chat-style interface
- AI-style structured extraction
- Planning before execution
- Real UI automation against a controlled local system
- Human-in-the-loop approval before commit
- Successful submission with a receipt ID
- Write-back into the original conversation flow

## Product Framing

ClawSubmit is not a note-taking assistant.

ClawSubmit is not a workflow logger.

ClawSubmit is a demo product that shows what it looks like when an agent can:

- understand work
- plan work
- operate software
- wait for approval
- finish the task
- report the outcome back

## Tech Stack

- `Frontend`: React + Vite
- `Backend`: FastAPI
- `Automation`: Playwright
- `Execution Target`: local sandbox expense system
- `Mode`: local-only, deterministic, demo-stable

## Repo Structure

```text
clawsubmit/
├── backend/
│   ├── app/
│   └── tests/
├── frontend/
│   ├── src/
│   └── index.html
├── samples/
│   └── invoice.jpg
├── tests/
│   └── e2e/
├── package.json
└── playwright.config.js
```

## Local Run

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
PATH="/opt/homebrew/bin:$PATH" npm install --registry=https://registry.npmjs.org --strict-ssl=false
PATH="/opt/homebrew/bin:$PATH" npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

- `http://127.0.0.1:5173`

## Recommended Demo Path

For a smooth 3-minute hackathon recording, use this exact path:

1. Click `Use Sample`
2. Click `Parse`
3. Click `Apply Suggestion`
4. Click `Run Agent`
5. Click `Confirm Submit`

This path is intentionally fixed and stable:

- fixed parse result
- fixed plan result
- fixed receipt id
- deterministic execution logs
- local-only execution target
- short, smooth automation timing

## Example Write-Back

After submission, ClawSubmit writes this back into the chat panel:

```text
✅ 报销单已提交：BX-20260318-0042｜¥86.50｜市场部｜待审批
```

## Example Structured Output

```json
{
  "expense_type": "差旅-打车",
  "amount": "86.50",
  "date_time": "2026-03-18 21:30",
  "from_to": "虹桥 -> 公司",
  "project": "龙虾黑客松",
  "cost_center": "市场部",
  "summary": "",
  "summary_suggestion": "龙虾黑客松差旅打车",
  "attachment_path": "/samples/invoice.jpg"
}
```

## Why It Works Well For A Hackathon

- Easy to understand in one sentence
- Visually clear left-to-right workflow
- Shows real execution, not just reasoning
- Includes a human approval checkpoint
- Ends in a concrete business outcome
- Runs fully locally without external service risk

## If You Are Watching The Demo

The key thing to look for is not field extraction.

The key thing is the full loop:

**chat input -> structured data -> plan -> execution -> confirmation -> submission -> receipt -> write-back**

That is what ClawSubmit is built to demonstrate.
