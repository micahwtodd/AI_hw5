"""FastAPI routes and command-line entry point for Campus Customs."""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from typing import Any, Literal

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.audit import DEFAULT_AUDIT_PATH, summarize
from backend.team import AgentTeam, team_manifest

WORKING_DATABASE = _ROOT / "data" / "campus_customs_new.db"
ORIGINAL_DATABASE = _ROOT / "data" / "campus_customs.db"
CHECKING_ACCOUNT = "checking"

app = FastAPI(title="Campus Customs Operations")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ApprovalBody(BaseModel):
    ticket_id: int
    kind: Literal["invoice", "rent", "restock"]
    approved_by: str = Field(min_length=1)
    finish_review: bool = True


class RunBody(BaseModel):
    task: str | None = None


class DecisionBody(BaseModel):
    approved_by: str = Field(min_length=1)
    finish_review: bool = True


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _money(value: float) -> float:
    return round(float(value), 2)


def _one(connection: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
    row = connection.execute(sql, params).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="The requested shop record was not found.")
    return row


def _ticket_state(status: str) -> str:
    return "open" if status.casefold() == "open" else "resolved"


def _mark_ticket_resolved(ticket_id: int) -> None:
    """Mark a ticket resolved after a person acts. A finished agent run does not."""
    with closing(_connect(WORKING_DATABASE)) as connection:
        connection.execute(
            "UPDATE tickets SET status = 'resolved' WHERE id = ?",
            (ticket_id,),
        )
        connection.commit()


def _load_ticket(connection: sqlite3.Connection, ticket_id: int) -> dict[str, Any]:
    row = connection.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} was not found.")
    ticket = dict(row)
    ticket["state"] = _ticket_state(str(ticket["status"]))
    return ticket


def _checking(connection: sqlite3.Connection) -> sqlite3.Row:
    return _one(
        connection,
        """
        SELECT name, balance, date
        FROM cash_accounts
        WHERE name = ? COLLATE NOCASE
        """,
        (CHECKING_ACCOUNT,),
    )


def _desk_date(connection: sqlite3.Connection) -> str:
    row = _one(connection, "SELECT date_today FROM desk LIMIT 1")
    return str(row["date_today"])


def _vendor_for_product(connection: sqlite3.Connection, sku: str) -> sqlite3.Row:
    item = connection.execute(
        "SELECT name FROM inventory WHERE sku = ? ORDER BY size LIMIT 1",
        (sku,),
    ).fetchone()
    product_name = str(item["name"] if item is not None else sku)
    specialty = "%mug%" if "mug" in product_name.casefold() else "%apparel%"
    vendors = connection.execute(
        """
        SELECT id, name, specialty, lead_days
        FROM vendors
        WHERE specialty LIKE ? COLLATE NOCASE
        ORDER BY lead_days, id
        """,
        (specialty,),
    ).fetchall()
    if len(vendors) != 1:
        raise HTTPException(
            status_code=409,
            detail=(
                f"The database does not identify exactly one vendor for {sku}. "
                "No purchase amount was created."
            ),
        )
    return vendors[0]


def _refuse_negative_cash(balance: float, amount: float) -> None:
    if _money(balance - amount) < 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Checking has ${_money(balance):.2f}. "
                f"A ${_money(amount):.2f} payment would make it negative, so it was refused."
            ),
        )


def _record_payment(
    connection: sqlite3.Connection,
    *,
    kind: str,
    ref_id: int,
    amount: float,
    approved_by: str,
    paid_at: str,
) -> int:
    cash = _checking(connection)
    balance = float(cash["balance"])
    _refuse_negative_cash(balance, amount)
    new_balance = _money(balance - amount)
    cursor = connection.execute(
        """
        INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (kind, ref_id, amount, CHECKING_ACCOUNT, paid_at, approved_by),
    )
    connection.execute(
        """
        UPDATE cash_accounts
        SET balance = ?, date = ?
        WHERE name = ? COLLATE NOCASE
        """,
        (new_balance, paid_at, CHECKING_ACCOUNT),
    )
    return int(cursor.lastrowid)


def _approve_invoice(
    connection: sqlite3.Connection,
    ticket: dict[str, Any],
    approved_by: str,
    paid_at: str,
) -> dict[str, Any]:
    invoice_id = ticket["invoice_id"]
    if invoice_id is None:
        raise HTTPException(status_code=409, detail="This ticket has no invoice to pay.")
    invoice = _one(
        connection,
        """
        SELECT id, vendor_id, amount, status, description
        FROM invoices
        WHERE id = ?
        """,
        (invoice_id,),
    )
    if str(invoice["status"]).casefold() != "open":
        raise HTTPException(status_code=409, detail=f"Invoice {invoice_id} is already {invoice['status']}.")
    amount = _money(invoice["amount"])
    balance_before = _money(_checking(connection)["balance"])
    payment_id = _record_payment(
        connection,
        kind="invoice",
        ref_id=int(invoice["id"]),
        amount=amount,
        approved_by=approved_by,
        paid_at=paid_at,
    )
    connection.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (invoice["id"],))
    return {
        "approved": True,
        "payment_id": payment_id,
        "kind": "invoice",
        "ticket_id": ticket["id"],
        "ref_id": int(invoice["id"]),
        "description": invoice["description"],
        "amount": amount,
        "account": CHECKING_ACCOUNT,
        "balance_before": balance_before,
        "balance_after": _money(balance_before - amount),
        "approved_by": approved_by,
        "paid_at": paid_at,
    }


def _approve_rent(
    connection: sqlite3.Connection,
    ticket: dict[str, Any],
    approved_by: str,
    paid_at: str,
) -> dict[str, Any]:
    lease_id = ticket["lease_id"]
    if lease_id is None:
        raise HTTPException(status_code=409, detail="This ticket has no lease to pay.")
    existing = connection.execute(
        """
        SELECT id FROM payments
        WHERE kind = 'rent' AND ref_id = ?
        """,
        (lease_id,),
    ).fetchone()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Rent for lease {lease_id} is already paid.")
    lease = _one(
        connection,
        "SELECT id, space_name, landlord, monthly_rent FROM leases WHERE id = ?",
        (lease_id,),
    )
    amount = _money(lease["monthly_rent"])
    balance_before = _money(_checking(connection)["balance"])
    payment_id = _record_payment(
        connection,
        kind="rent",
        ref_id=int(lease["id"]),
        amount=amount,
        approved_by=approved_by,
        paid_at=paid_at,
    )
    return {
        "approved": True,
        "payment_id": payment_id,
        "kind": "rent",
        "ticket_id": ticket["id"],
        "ref_id": int(lease["id"]),
        "description": f"{lease['space_name']} rent to {lease['landlord']}",
        "amount": amount,
        "account": CHECKING_ACCOUNT,
        "balance_before": balance_before,
        "balance_after": _money(balance_before - amount),
        "approved_by": approved_by,
        "paid_at": paid_at,
    }


def _approve_restock(
    connection: sqlite3.Connection,
    ticket: dict[str, Any],
    approved_by: str,
    paid_at: str,
) -> dict[str, Any]:
    sku = ticket["sku"]
    size = ticket["size"]
    if not sku or not size or ticket["qty"] is None:
        raise HTTPException(status_code=409, detail="This ticket has no SKU, size, and quantity to restock.")
    existing = connection.execute(
        "SELECT id FROM payments WHERE kind = 'restock' AND ref_id = ?",
        (ticket["id"],),
    ).fetchone()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Ticket {ticket['id']} already has an approved restock.")
    stock = connection.execute(
        "SELECT qty FROM inventory WHERE sku = ? AND size = ?",
        (sku, size),
    ).fetchone()
    if stock is None:
        raise HTTPException(status_code=404, detail=f"No inventory row exists for {sku} size {size}.")
    shortfall = int(ticket["qty"]) - int(stock["qty"])
    if shortfall <= 0:
        raise HTTPException(
            status_code=409,
            detail=f"{sku} size {size} already has enough stock. No restock payment was created.",
        )
    pricing = _one(connection, "SELECT unit_cost FROM pricing WHERE sku = ?", (sku,))
    unit_cost = _money(pricing["unit_cost"])
    amount = _money(shortfall * unit_cost)
    vendor = _vendor_for_product(connection, str(sku))
    open_invoices = connection.execute(
        """
        SELECT id, amount
        FROM invoices
        WHERE vendor_id = ? AND status = 'open' COLLATE NOCASE
        ORDER BY id
        """,
        (vendor["id"],),
    ).fetchall()
    if open_invoices:
        bills = ", ".join(f"invoice {row['id']} for ${_money(row['amount']):.2f}" for row in open_invoices)
        raise HTTPException(
            status_code=409,
            detail=(
                f"{vendor['name']} will not ship a new order while {bills} is open. "
                "Pay that bill first. No restock payment was created."
            ),
        )
    balance_before = _money(_checking(connection)["balance"])
    payment_id = _record_payment(
        connection,
        kind="restock",
        ref_id=int(ticket["id"]),
        amount=amount,
        approved_by=approved_by,
        paid_at=paid_at,
    )
    connection.execute(
        "UPDATE inventory SET qty = qty + ? WHERE sku = ? AND size = ?",
        (shortfall, sku, size),
    )
    return {
        "approved": True,
        "payment_id": payment_id,
        "kind": "restock",
        "ticket_id": ticket["id"],
        "ref_id": int(ticket["id"]),
        "sku": sku,
        "size": size,
        "quantity": shortfall,
        "unit_cost": unit_cost,
        "vendor_id": int(vendor["id"]),
        "vendor_name": vendor["name"],
        "amount": amount,
        "account": CHECKING_ACCOUNT,
        "balance_before": balance_before,
        "balance_after": _money(balance_before - amount),
        "approved_by": approved_by,
        "paid_at": paid_at,
    }


def _apply_approval(body: ApprovalBody) -> dict[str, Any]:
    approved_by = body.approved_by.strip()
    if not approved_by:
        raise HTTPException(status_code=422, detail="approved_by is required.")
    with closing(_connect(WORKING_DATABASE)) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            ticket = _load_ticket(connection, body.ticket_id)
            if str(ticket["status"]).casefold() != "open":
                raise HTTPException(status_code=409, detail="This ticket is already resolved.")
            paid_at = _desk_date(connection)
            if body.kind == "invoice":
                result = _approve_invoice(connection, ticket, approved_by, paid_at)
            elif body.kind == "rent":
                result = _approve_rent(connection, ticket, approved_by, paid_at)
            else:
                result = _approve_restock(connection, ticket, approved_by, paid_at)
            if body.finish_review:
                connection.execute(
                    "UPDATE tickets SET status = 'resolved' WHERE id = ?",
                    (int(ticket["id"]),),
                )
                result["ticket_state"] = "resolved"
            else:
                result["ticket_state"] = "open"
            connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise


@app.get("/api/tickets")
def list_tickets() -> dict[str, Any]:
    """Return tickets 101, 102, and 103 with an open or resolved state."""
    with closing(_connect(WORKING_DATABASE)) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM tickets
            WHERE id IN (101, 102, 103)
            ORDER BY id
            """
        ).fetchall()
        prices = connection.execute("SELECT sku, unit_cost, list_price FROM pricing").fetchall()
    by_sku = {str(row["sku"]): row for row in prices}
    tickets = []
    for row in rows:
        ticket = dict(row)
        ticket["state"] = _ticket_state(str(ticket["status"]))
        price = by_sku.get(str(ticket.get("sku") or ""))
        if price is not None:
            ticket["unit_cost"] = _money(price["unit_cost"])
            ticket["list_price"] = _money(price["list_price"])
        tickets.append(ticket)
    return {"count": len(tickets), "tickets": tickets}


@app.post("/api/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int, body: RunBody | None = None) -> dict[str, Any]:
    """Run the Boss and the specialist team on one ticket."""
    with closing(_connect(WORKING_DATABASE)) as connection:
        _load_ticket(connection, ticket_id)
    team = AgentTeam()
    try:
        result = await team.run_ticket(ticket_id, task=None if body is None else body.task)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=summarize(str(exc))) from exc
    payload = result.model_dump(mode="json")
    payload["ticket_state"] = "open"
    return payload


@app.get("/api/events")
def list_events(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    """Return recent audit events for the operations board."""
    path = DEFAULT_AUDIT_PATH
    if not path.is_file() or path.stat().st_size == 0:
        return {"count": 0, "total_count": 0, "events": []}
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Audit trail is unreadable. It was left unchanged.",
        ) from exc
    if not isinstance(existing, list):
        raise HTTPException(status_code=500, detail="Audit trail must be a JSON list. It was left unchanged.")
    recent = existing[-limit:]
    return {"count": len(recent), "total_count": len(existing), "events": recent}


@app.post("/api/approvals")
def approve_payment(body: ApprovalBody) -> dict[str, Any]:
    """Record a human-approved payment, reduce checking cash, and resolve the ticket."""
    return _apply_approval(body)


def _close_without_cash(ticket_id: int, approved_by: str, finish_review: bool = True) -> dict[str, Any]:
    """Record a human decision that does not move cash."""
    name = approved_by.strip()
    if not name:
        raise HTTPException(status_code=422, detail="approved_by is required.")
    with closing(_connect(WORKING_DATABASE)) as connection:
        ticket = _load_ticket(connection, ticket_id)
        if str(ticket["status"]).casefold() != "open":
            raise HTTPException(status_code=409, detail="This ticket is already resolved.")
    if finish_review:
        _mark_ticket_resolved(ticket_id)
    return {
        "ticket_id": ticket_id,
        "ticket_state": "resolved" if finish_review else "open",
        "approved_by": name,
        "cash_changed": False,
    }


@app.post("/api/tickets/{ticket_id}/decision")
def record_decision(ticket_id: int, body: DecisionBody) -> dict[str, Any]:
    """Resolve a ticket when a person records a note that does not move cash."""
    return _close_without_cash(ticket_id, body.approved_by, body.finish_review)


@app.post("/api/tickets/{ticket_id}/decline")
def decline_ticket(ticket_id: int, body: DecisionBody) -> dict[str, Any]:
    """Record that a person declined. Checking does not change."""
    return _close_without_cash(ticket_id, body.approved_by, body.finish_review)


@app.get("/api/cash")
def get_cash() -> dict[str, Any]:
    """Return the current checking balance."""
    with closing(_connect(WORKING_DATABASE)) as connection:
        cash = _checking(connection)
    return {
        "account": cash["name"],
        "balance": _money(cash["balance"]),
        "date": cash["date"],
    }


@app.post("/api/reset")
def reset_database() -> dict[str, Any]:
    """Restore the working database from the original campus_customs.db file."""
    if not ORIGINAL_DATABASE.is_file():
        raise HTTPException(status_code=404, detail="The original database is missing.")
    source = sqlite3.connect(ORIGINAL_DATABASE)
    try:
        with closing(_connect(WORKING_DATABASE)) as target:
            source.backup(target)
    finally:
        source.close()
    with closing(_connect(WORKING_DATABASE)) as connection:
        cash = _checking(connection)
    return {
        "reset": True,
        "working_database": WORKING_DATABASE.name,
        "original_database": ORIGINAL_DATABASE.name,
        "checking_balance": _money(cash["balance"]),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Campus Customs agent team.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ticket = subparsers.add_parser("ticket", help="Coordinate one ticket through the Boss.")
    ticket.add_argument("ticket_id", type=int)
    ticket.add_argument("--task", help="Optional custom task for this ticket.")

    subparsers.add_parser(
        "all",
        help="Verify the database reset, then coordinate every open ticket.",
    )
    subparsers.add_parser(
        "manifest",
        help="Print the secret-free team configuration without calling a model.",
    )
    return parser


async def _run(args: argparse.Namespace) -> object:
    if args.command == "manifest":
        return team_manifest()

    team = AgentTeam()
    if args.command == "ticket":
        result = await team.run_ticket(args.ticket_id, task=args.task)
        return result.model_dump(mode="json")
    results = await team.run_all_open_tickets()
    return [result.model_dump(mode="json") for result in results]


def main() -> int:
    args = _parser().parse_args()
    try:
        result = asyncio.run(_run(args))
    except Exception as exc:
        print(f"{type(exc).__name__}: {summarize(str(exc))}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
