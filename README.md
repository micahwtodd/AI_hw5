# Campus Customs

Multi-agent shop desk for MGT 409E. Five agents read the shop database through a read-only MCP server. A human approves any payment. Only that approval changes cash.

The model for every agent is `gpt-6-luna`, called through Portkey. The key stays in a local `.env` file and is not part of this repository.

## Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace `your_key_here` with your own `PORTKEY_API_KEY`. Do not commit `.env` or paste the key into source, prompts, logs, or chat.

On macOS or Linux, create the environment with `python3 -m venv .venv` and install with `.venv/bin/python -m pip install -r requirements.txt`. Also change the Python command in `.mcp.json` and `.cursor/mcp.json` from `.venv/Scripts/python.exe` to `.venv/bin/python`.

The React desk needs its own packages:

```powershell
cd frontend
npm install
```

## Databases

Both shop files are in `data/`.

- `data/campus_customs.db` is the original shop. Checking is $3,400 and tickets 101, 102, and 103 are open. Leave this file unchanged.
- `data/campus_customs_new.db` is the working copy. The copy in this repo is the finished homework run: invoice 501 and lease 1 are paid, checking is $160, and all three tickets are resolved.

For a clean run, copy the original over the working file while the API is stopped:

```powershell
Copy-Item data\campus_customs.db data\campus_customs_new.db -Force
```

You can also restore the working file after the API is running. Use **Reset shop** on the board, or:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/reset
```

Reset copies `campus_customs.db` onto `campus_customs_new.db`. Do that before a full three-ticket run. A single ticket can be run again without a reset, but the three-ticket path starts from the original $3,400 balance.

## Run

The MCP server is `mcp_server/server.py`. It speaks MCP over standard input. Cursor starts it from `.mcp.json`. A ticket run starts its own copy from `backend/team.py`, so the board does not need a separate MCP terminal. To start it yourself from the project root:

```powershell
.\.venv\Scripts\python.exe mcp_server\server.py
```

That process waits for a client. It does not open a port.

Start the API and the board in two terminals.

1. FastAPI backend, from `backend/`:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

The API is http://127.0.0.1:8000.

2. React board, from `frontend/`:

```powershell
cd frontend
npm run dev
```

Open http://localhost:5173. Use that host, not `[::1]`. The API allows the Vite origin on port 5173.

Before running tickets 101, 102, and 103 as a set, click **Reset shop**. Checking should read $3,400.00 and the shop date should read 2026-08-31.
