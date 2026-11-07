# Campus Customs MCP Server

This FastMCP server gives the Campus Customs agent team a shared set of database-grounded tools. It uses `data/campus_customs_new.db`, opened in read-only mode, and does not invent missing records or values.

## Tools

- `check_inventory_status(...)` accepts a ticket or direct SKU/size inputs, reads `tickets` and `inventory`, and returns exact stock plus a shortfall when a requested quantity is known.
- `check_pricing_and_margin(...)` accepts a ticket or direct SKU, reads `tickets` and `pricing`, and returns stored prices plus deterministic order and proposed-price calculations.
- `draft_payment_for_human_review(...)` accepts a ticket, invoice, lease, or payment kind; reads `tickets`, `invoices`, `leases`, `cash_accounts`, and `desk`; and returns a non-executable proposal with the projected cash balance.
- `list_open_tickets(...)` reads `tickets` and returns exact ticket records filtered by status and optional type.
- `list_invoices(...)` reads `invoices` and returns exact records filtered by status and optional vendor.
- `get_cash_status(...)` reads `cash_accounts` and `desk`; it returns recorded account balances and their total without modeling inflows or changing cash.
- `get_lease_status(...)` reads `leases` and `desk`; it calculates due timing from `desk.date_today`, never from the computer clock.
- `check_vendor_status(...)` reads `vendors` and `invoices`; it returns stored lead times and whether open invoices block shipping under the shop rule.
- `verify_database_reset()` compares logical SHA-256 digests of the baseline `campus_customs.db` and working `campus_customs_new.db` without modifying either file.

The payment tool never approves or executes payments, writes payment records, or changes cash. Human approval remains mandatory.

The database has no vendor-to-SKU map or vendor product costs. `check_vendor_status` reports those limits explicitly instead of claiming that a vendor can supply a particular item or inventing a cost.

## Connection

The server is defined in `server.py` and uses local STDIO transport. `.mcp.json` at the project root is the connection file, and it contains no API key. The same connection is also in `.cursor/mcp.json` so Cursor can launch it. The PydanticAI team in `backend/team.py` starts this same server when a ticket runs. There is no separate database-access layer in the backend.

On macOS or Linux, change the command in those JSON files from `.venv/Scripts/python.exe` to `.venv/bin/python`.
