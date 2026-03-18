# clawsubmit

Local MVP demo for an execution-native productivity agent in an OpenClaw-style workflow.

## Apps

- `frontend/`: React + Vite operations console
- `backend/`: FastAPI APIs, sandbox expense pages, and Playwright coordinator

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
PATH="/opt/homebrew/bin:$PATH" npm install
PATH="/opt/homebrew/bin:$PATH" npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).
