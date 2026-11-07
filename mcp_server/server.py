"""Read-only FastMCP tools for Campus Customs operations."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Any, Literal

from fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "campus_customs_new.db"
ORIGINAL_DATABASE_PATH = PROJECT_ROOT / "data" / "campus_customs.db"

mcp = FastMCP(name="Campus Customs Operations")


def _connect_path(path: Path) -> sqlite3.Connection:
    """Open one SQLite database in read-only, query-only mode."""
    if not path.is_file():
        raise FileNotFoundError(f"Database not found: {path}")

    connection = sqlite3.connect(
        f"file:{path.as_posix()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def _connect() -> sqlite3.Connection:
    """Open the working homework database."""
    return _connect_path(DATABASE_PATH)


def _require_ticket(connection: sqlite3.Connection, ticket_id: int) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT id, type, requester, subject, sku, size, qty, lease_id,
               invoice_id, status, notes, created_at
        FROM tickets
        WHERE id = ?
        """,
        (ticket_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Ticket {ticket_id} was not found.")
    return dict(row)


def _rounded_money(value: float) -> float:
    return round(float(value), 2)


def _normalized_code(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized or None


def _matching_tickets(
    connection: sqlite3.Connection,
    *,
    sku: str,
    size: str | None = None,
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT id, type, requester, subject, sku, size, qty, lease_id,
               invoice_id, status, notes, created_at
        FROM tickets
        WHERE status = 'open'
          AND sku = ? COLLATE NOCASE
          AND (? IS NULL OR size = ? COLLATE NOCASE)
        ORDER BY id
        """,
        (sku, size, size),
    ).fetchall()
    return [dict(row) for row in rows]


def _check_inventory_status(
    ticket_id: int | None = None,
    sku: str | None = None,
    size: str | None = None,
    requested_qty: int | None = None,
) -> dict[str, Any]:
    direct_sku = _normalized_code(sku)
    direct_size = _normalized_code(size)
    if requested_qty is not None and requested_qty < 0:
        raise ValueError("requested_qty cannot be negative.")
    if requested_qty is not None and direct_size is None and ticket_id is None:
        raise ValueError("Provide a size when checking a requested quantity.")

    with closing(_connect()) as connection:
        ticket = _require_ticket(connection, ticket_id) if ticket_id is not None else None
        if ticket is not None:
            ticket_sku = _normalized_code(ticket["sku"])
            ticket_size = _normalized_code(ticket["size"])
            if direct_sku is not None and direct_sku != ticket_sku:
                raise ValueError("The supplied SKU conflicts with the ticket SKU.")
            if direct_size is not None and direct_size != ticket_size:
                raise ValueError("The supplied size conflicts with the ticket size.")
            if (
                requested_qty is not None
                and ticket["qty"] is not None
                and requested_qty != int(ticket["qty"])
            ):
                raise ValueError(
                    "The supplied requested quantity conflicts with the ticket quantity."
                )
            resolved_sku = direct_sku or ticket_sku
            resolved_size = direct_size or ticket_size
            resolved_qty = (
                requested_qty
                if requested_qty is not None
                else ticket["qty"]
            )
            matching_tickets = [ticket]
        else:
            if direct_sku is None:
                raise ValueError("Provide ticket_id or sku.")
            matching_tickets = _matching_tickets(
                connection,
                sku=direct_sku,
                size=direct_size,
            )
            matched_ticket = matching_tickets[0] if len(matching_tickets) == 1 else None
            resolved_sku = direct_sku
            resolved_size = direct_size
            resolved_qty = (
                requested_qty
                if requested_qty is not None
                else (matched_ticket["qty"] if matched_ticket is not None else None)
            )
            ticket = matched_ticket

        rows = connection.execute(
            """
            SELECT sku, name, size, qty, location
            FROM inventory
            WHERE sku = ? COLLATE NOCASE
            ORDER BY size
            """,
            (resolved_sku,),
        ).fetchall()

    all_sizes = [dict(row) for row in rows]
    base_result: dict[str, Any] = {
        "source_tables": ["tickets", "inventory"],
        "ticket_id": ticket["id"] if ticket is not None else None,
        "matching_ticket_ids": [item["id"] for item in matching_tickets],
        "ticket_status": ticket["status"] if ticket is not None else None,
        "sku": resolved_sku,
        "requested_size": resolved_size,
        "requested_qty": int(resolved_qty) if resolved_qty is not None else None,
    }
    if resolved_size is None:
        base_result.update(
            {
                "sizes": [
                    {
                        "size": row["size"],
                        "qty": int(row["qty"]),
                        "location": row["location"],
                    }
                    for row in all_sizes
                ],
                "inventory_record_found": bool(all_sizes),
                "available_qty": None,
                "shortfall_qty": None,
                "can_fulfill_from_stock": None,
            }
        )
        return base_result

    requested_record = next(
        (
            row
            for row in all_sizes
            if _normalized_code(row["size"]) == resolved_size
        ),
        None,
    )
    if requested_record is None:
        base_result.update(
            {
                "inventory_record_found": False,
                "available_qty": None,
                "shortfall_qty": None,
                "can_fulfill_from_stock": None,
            }
        )
        return base_result

    available_qty = int(requested_record["qty"])
    shortfall_qty = (
        max(int(resolved_qty) - available_qty, 0)
        if resolved_qty is not None
        else None
    )
    base_result.update(
        {
            "product_name": requested_record["name"],
            "inventory_record_found": True,
            "available_qty": available_qty,
            "shortfall_qty": shortfall_qty,
            "can_fulfill_from_stock": (
                shortfall_qty == 0 if shortfall_qty is not None else None
            ),
            "location": requested_record["location"],
        }
    )
    return base_result


@mcp.tool
def check_inventory_status(
    ticket_id: int | None = None,
    sku: str | None = None,
    size: str | None = None,
    requested_qty: int | None = None,
) -> dict[str, Any]:
    """Return stock for the requested size, with the shortfall when quantity is known.

    Reads only the tickets and inventory tables. A request with a size returns that
    size only. Omitting size returns each size's quantity. It does not reserve stock,
    order stock, alter quantities, or infer a missing inventory record as zero.

    Args:
        ticket_id: Optional ticket whose SKU, size, and quantity should be used.
        sku: Optional direct SKU lookup, such as CC-TEE-WHITE.
        size: Optional size lookup. Omit it to return each size and quantity.
        requested_qty: Optional quantity used to calculate a stock shortfall.
    """
    return _check_inventory_status(ticket_id, sku, size, requested_qty)


def _bulk_price_options(
    unit_cost: float,
    list_price: float,
    quantity: int | None,
) -> list[dict[str, Any]]:
    """List the shelf price and any standard bulk steps that stay above cost."""
    prices = [list_price]
    for choice in (50.0, 45.0, 40.0):
        if unit_cost < choice < list_price:
            prices.append(choice)
    options = []
    for price in prices:
        unit_price = _rounded_money(price)
        profit = _rounded_money(unit_price - unit_cost)
        margin = round((profit / unit_price) * 100, 2) if unit_price else None
        total = _rounded_money(unit_price * int(quantity)) if quantity is not None else None
        options.append(
            {
                "unit_price": unit_price,
                "per_unit_gross_profit": profit,
                "gross_margin_percent": margin,
                "total_for_quantity": total,
                "approved": False,
                "label": "stored list price" if unit_price == list_price else "proposed bulk price",
            }
        )
    return options


def _check_pricing_and_margin(
    ticket_id: int | None = None,
    sku: str | None = None,
    quantity: int | None = None,
    proposed_unit_price: float | None = None,
) -> dict[str, Any]:
    direct_sku = _normalized_code(sku)
    if quantity is not None and quantity < 0:
        raise ValueError("quantity cannot be negative.")
    if proposed_unit_price is not None and proposed_unit_price < 0:
        raise ValueError("proposed_unit_price cannot be negative.")

    with closing(_connect()) as connection:
        ticket = _require_ticket(connection, ticket_id) if ticket_id is not None else None
        if ticket is not None:
            ticket_sku = _normalized_code(ticket["sku"])
            if direct_sku is not None and direct_sku != ticket_sku:
                raise ValueError("The supplied SKU conflicts with the ticket SKU.")
            if (
                quantity is not None
                and ticket["qty"] is not None
                and quantity != int(ticket["qty"])
            ):
                raise ValueError(
                    "The supplied quantity conflicts with the ticket quantity."
                )
            resolved_sku = direct_sku or ticket_sku
            resolved_qty = quantity if quantity is not None else ticket["qty"]
            matching_tickets = [ticket]
        else:
            if direct_sku is None:
                raise ValueError("Provide ticket_id or sku.")
            matching_tickets = _matching_tickets(connection, sku=direct_sku)
            matched_ticket = matching_tickets[0] if len(matching_tickets) == 1 else None
            resolved_sku = direct_sku
            resolved_qty = (
                quantity
                if quantity is not None
                else (matched_ticket["qty"] if matched_ticket is not None else None)
            )
            ticket = matched_ticket

        pricing_row = connection.execute(
            """
            SELECT sku, unit_cost, list_price
            FROM pricing
            WHERE sku = ? COLLATE NOCASE
            """,
            (resolved_sku,),
        ).fetchone()

    if pricing_row is None:
        return {
            "source_tables": ["tickets", "pricing"],
            "ticket_id": ticket["id"] if ticket is not None else None,
            "matching_ticket_ids": [item["id"] for item in matching_tickets],
            "ticket_status": ticket["status"] if ticket is not None else None,
            "sku": resolved_sku,
            "requested_qty": int(resolved_qty) if resolved_qty is not None else None,
            "pricing_record_found": False,
            "unit_cost": None,
            "list_price": None,
            "total_cost": None,
            "total_at_list_price": None,
            "gross_profit_at_list_price": None,
            "gross_margin_percent_at_list_price": None,
        }

    pricing = dict(pricing_row)
    unit_cost = _rounded_money(pricing["unit_cost"])
    list_price = _rounded_money(pricing["list_price"])
    per_unit_gross_profit = _rounded_money(list_price - unit_cost)
    per_unit_gross_margin = (
        round((per_unit_gross_profit / list_price) * 100, 2)
        if list_price
        else None
    )

    result: dict[str, Any] = {
        "source_tables": ["tickets", "pricing"],
        "ticket_id": ticket["id"] if ticket is not None else None,
        "matching_ticket_ids": [item["id"] for item in matching_tickets],
        "ticket_status": ticket["status"] if ticket is not None else None,
        "sku": resolved_sku,
        "requested_qty": int(resolved_qty) if resolved_qty is not None else None,
        "pricing_record_found": True,
        "unit_cost": unit_cost,
        "list_price": list_price,
        "per_unit_gross_profit_at_list_price": per_unit_gross_profit,
        "gross_margin_percent_at_list_price": per_unit_gross_margin,
    }
    if resolved_qty is None:
        result.update(
            {
                "total_cost": None,
                "total_at_list_price": None,
                "gross_profit_at_list_price": None,
            }
        )
    else:
        resolved_quantity = int(resolved_qty)
        result.update(
            {
                "total_cost": _rounded_money(unit_cost * resolved_quantity),
                "total_at_list_price": _rounded_money(
                    list_price * resolved_quantity
                ),
                "gross_profit_at_list_price": _rounded_money(
                    per_unit_gross_profit * resolved_quantity
                ),
            }
        )

    if proposed_unit_price is not None:
        proposed_price = _rounded_money(proposed_unit_price)
        proposed_profit = _rounded_money(proposed_price - unit_cost)
        proposed_margin = (
            round((proposed_profit / proposed_price) * 100, 2)
            if proposed_price
            else None
        )
        result["proposed_price_analysis"] = {
            "input_source": "caller_provided",
            "proposed_unit_price": proposed_price,
            "per_unit_gross_profit": proposed_profit,
            "gross_margin_percent": proposed_margin,
            "below_unit_cost": proposed_price < unit_cost,
            "total_at_proposed_price": (
                _rounded_money(proposed_price * int(resolved_qty))
                if resolved_qty is not None
                else None
            ),
            "total_gross_profit": (
                _rounded_money(proposed_profit * int(resolved_qty))
                if resolved_qty is not None
                else None
            ),
        }
    else:
        result["proposed_price_analysis"] = None
    if ticket is not None and str(ticket["type"]).casefold() == "price_override":
        result["price_options"] = _bulk_price_options(unit_cost, list_price, resolved_qty)
        result["price_options_note"] = (
            "Proposals calculated from the stored unit cost and list price. None is approved."
        )
    else:
        result["price_options"] = None
    return result


@mcp.tool
def check_pricing_and_margin(
    ticket_id: int | None = None,
    sku: str | None = None,
    quantity: int | None = None,
    proposed_unit_price: float | None = None,
) -> dict[str, Any]:
    """Return stored pricing and deterministic gross-margin calculations.

    Reads only the tickets and pricing tables. It can use a ticket or direct SKU.
    A caller-provided proposed price is clearly labelled and never approved.
    A price_override ticket also returns price_options from the stored cost and list price. None of those options is approved.

    Args:
        ticket_id: Optional ticket whose SKU and quantity should be used.
        sku: Optional direct SKU lookup, such as CC-HOOD-NAVY.
        quantity: Optional quantity used for order-level calculations.
        proposed_unit_price: Optional hypothetical price to evaluate, not approve.
    """
    return _check_pricing_and_margin(
        ticket_id,
        sku,
        quantity,
        proposed_unit_price,
    )


def _draft_payment_for_human_review(
    ticket_id: int | None = None,
    invoice_id: int | None = None,
    lease_id: int | None = None,
    payment_kind: Literal["invoice", "rent"] | None = None,
    account_name: str = "checking",
) -> dict[str, Any]:
    normalized_account = account_name.strip()
    if not normalized_account:
        raise ValueError("account_name cannot be blank.")
    if invoice_id is not None and lease_id is not None:
        raise ValueError("Provide invoice_id or lease_id, not both.")

    with closing(_connect()) as connection:
        ticket = _require_ticket(connection, ticket_id) if ticket_id is not None else None
        desk = connection.execute(
            "SELECT date_today, notes FROM desk LIMIT 1"
        ).fetchone()
        if desk is None:
            raise ValueError("The desk table does not contain date_today.")

        account = connection.execute(
            """
            SELECT name, balance, date
            FROM cash_accounts
            WHERE name = ? COLLATE NOCASE
            """,
            (normalized_account,),
        ).fetchone()
        if account is None:
            raise ValueError(f"Cash account {normalized_account!r} was not found.")

        if ticket is not None:
            ticket_invoice_id = ticket["invoice_id"]
            ticket_lease_id = ticket["lease_id"]
            if ticket_invoice_id is not None and ticket_lease_id is not None:
                raise ValueError(
                    f"Ticket {ticket_id} references both an invoice and a lease; "
                    "a human must resolve the ambiguity."
                )
            if invoice_id is not None and invoice_id != ticket_invoice_id:
                raise ValueError(
                    "The supplied invoice_id conflicts with the ticket invoice."
                )
            if lease_id is not None and lease_id != ticket_lease_id:
                raise ValueError(
                    "The supplied lease_id conflicts with the ticket lease."
                )
            resolved_invoice_id = invoice_id or ticket_invoice_id
            resolved_lease_id = lease_id or ticket_lease_id
            selection_method = "ticket"
        else:
            resolved_invoice_id = invoice_id
            resolved_lease_id = lease_id
            selection_method = "invoice_id" if invoice_id is not None else "lease_id"

        if (
            resolved_invoice_id is None
            and resolved_lease_id is None
            and payment_kind is None
        ):
            raise ValueError(
                "Provide ticket_id, invoice_id, lease_id, or payment_kind."
            )

        if (
            resolved_invoice_id is None
            and resolved_lease_id is None
            and payment_kind == "invoice"
        ):
            bill_row = connection.execute(
                """
                SELECT id
                FROM invoices
                WHERE status = 'open'
                ORDER BY date(due_date), id
                LIMIT 1
                """
            ).fetchone()
            if bill_row is None:
                raise ValueError("No open invoice was found.")
            resolved_invoice_id = bill_row["id"]
            selection_method = "earliest_open_invoice"
        elif (
            resolved_invoice_id is None
            and resolved_lease_id is None
            and payment_kind == "rent"
        ):
            bill_row = connection.execute(
                """
                SELECT id
                FROM leases
                ORDER BY date(next_due), id
                LIMIT 1
                """
            ).fetchone()
            if bill_row is None:
                raise ValueError("No lease was found.")
            resolved_lease_id = bill_row["id"]
            selection_method = "earliest_lease_due"

        if resolved_invoice_id is not None:
            if payment_kind is not None and payment_kind != "invoice":
                raise ValueError(
                    "payment_kind conflicts with the selected invoice."
                )
            bill_row = connection.execute(
                """
                SELECT id, vendor_id, amount, due_date, status, description
                FROM invoices
                WHERE id = ?
                """,
                (resolved_invoice_id,),
            ).fetchone()
            if bill_row is None:
                raise ValueError(f"Invoice {resolved_invoice_id} was not found.")
            bill = dict(bill_row)
            resolved_payment_kind = "invoice"
            reference_id = bill["id"]
            amount = _rounded_money(bill["amount"])
            due_date_text = bill["due_date"]
            payee_reference = {"vendor_id": bill["vendor_id"]}
            bill_status = bill["status"]
            description = bill["description"]
        elif resolved_lease_id is not None:
            if payment_kind is not None and payment_kind != "rent":
                raise ValueError("payment_kind conflicts with the selected lease.")
            bill_row = connection.execute(
                """
                SELECT id, space_name, landlord, monthly_rent, next_due, notes
                FROM leases
                WHERE id = ?
                """,
                (resolved_lease_id,),
            ).fetchone()
            if bill_row is None:
                raise ValueError(f"Lease {resolved_lease_id} was not found.")
            bill = dict(bill_row)
            resolved_payment_kind = "rent"
            reference_id = bill["id"]
            amount = _rounded_money(bill["monthly_rent"])
            due_date_text = bill["next_due"]
            payee_reference = {
                "landlord": bill["landlord"],
                "space_name": bill["space_name"],
            }
            bill_status = None
            description = bill["notes"]
        else:
            raise ValueError("No invoice or lease could be resolved.")

        if ticket is None:
            reference_column = (
                "invoice_id"
                if resolved_payment_kind == "invoice"
                else "lease_id"
            )
            related_tickets = connection.execute(
                f"""
                SELECT id, type, requester, subject, sku, size, qty, lease_id,
                       invoice_id, status, notes, created_at
                FROM tickets
                WHERE {reference_column} = ? AND status = 'open'
                ORDER BY id
                """,
                (reference_id,),
            ).fetchall()
            if len(related_tickets) == 1:
                ticket = dict(related_tickets[0])
        else:
            related_tickets = []

    today = date.fromisoformat(desk["date_today"])
    due_date = date.fromisoformat(due_date_text)
    days_until_due = (due_date - today).days
    current_balance = _rounded_money(account["balance"])
    projected_balance = _rounded_money(current_balance - amount)
    cash_sufficient = projected_balance >= 0
    bill_is_open = bill_status in (None, "open")

    blocking_reason = None
    if not bill_is_open:
        blocking_reason = f"bill_status_is_{bill_status}"
    elif not cash_sufficient:
        blocking_reason = "insufficient_cash"

    return {
        "source_tables": [
            "tickets",
            "invoices",
            "leases",
            "cash_accounts",
            "desk",
        ],
        "ticket_id": ticket["id"] if ticket is not None else None,
        "related_ticket_ids": (
            [ticket["id"]]
            if ticket is not None
            else [row["id"] for row in related_tickets]
        ),
        "ticket_status": ticket["status"] if ticket is not None else None,
        "selection_method": selection_method,
        "payment_kind": resolved_payment_kind,
        "reference_id": reference_id,
        "payee_reference": payee_reference,
        "description": description,
        "amount": amount,
        "due_date": due_date_text,
        "date_today": desk["date_today"],
        "days_until_due": days_until_due,
        "is_overdue": days_until_due < 0,
        "bill_status": bill_status,
        "account": account["name"],
        "current_balance": current_balance,
        "projected_balance": projected_balance,
        "cash_sufficient": cash_sufficient,
        "ready_for_human_review": blocking_reason is None,
        "blocking_reason": blocking_reason,
        "human_approval_required": True,
        "approval_status": "pending_human_review",
        "payment_executed": False,
        "database_mutated": False,
    }


@mcp.tool
def draft_payment_for_human_review(
    ticket_id: int | None = None,
    invoice_id: int | None = None,
    lease_id: int | None = None,
    payment_kind: Literal["invoice", "rent"] | None = None,
    account_name: str = "checking",
) -> dict[str, Any]:
    """Prepare a payment proposal without approving or executing payment.

    Reads tickets, invoices, leases, cash_accounts, and desk. It can resolve a
    ticket, a specific bill, or the earliest stored rent or open invoice. It
    always checks projected cash and requires a human approver.

    Args:
        ticket_id: Optional ticket that references an invoice or lease.
        invoice_id: Optional invoice to review.
        lease_id: Optional lease whose rent should be reviewed.
        payment_kind: Optional "rent" or "invoice" lookup for the earliest due item.
        account_name: Cash account used for the projected-balance calculation.
    """
    return _draft_payment_for_human_review(
        ticket_id,
        invoice_id,
        lease_id,
        payment_kind,
        account_name,
    )


@mcp.tool
def list_open_tickets(
    status: str | None = "open",
    ticket_type: str | None = None,
) -> dict[str, Any]:
    """List tickets from the database without changing their status.

    Args:
        status: Ticket status to return. Use None to return every status.
        ticket_type: Optional exact ticket type such as customer_order.
    """
    normalized_status = status.strip() if status is not None else None
    normalized_type = ticket_type.strip() if ticket_type is not None else None
    with closing(_connect()) as connection:
        rows = connection.execute(
            """
            SELECT id, type, requester, subject, sku, size, qty, lease_id,
                   invoice_id, status, notes, created_at
            FROM tickets
            WHERE (? IS NULL OR status = ? COLLATE NOCASE)
              AND (? IS NULL OR type = ? COLLATE NOCASE)
            ORDER BY created_at, id
            """,
            (
                normalized_status,
                normalized_status,
                normalized_type,
                normalized_type,
            ),
        ).fetchall()
    tickets = [dict(row) for row in rows]
    return {
        "source_tables": ["tickets"],
        "filters": {
            "status": normalized_status,
            "ticket_type": normalized_type,
        },
        "count": len(tickets),
        "tickets": tickets,
    }


@mcp.tool
def list_invoices(
    status: str | None = "open",
    vendor_id: int | None = None,
) -> dict[str, Any]:
    """List exact invoice records, optionally filtered by status or vendor."""
    normalized_status = status.strip() if status is not None else None
    with closing(_connect()) as connection:
        rows = connection.execute(
            """
            SELECT id, vendor_id, amount, due_date, status, description
            FROM invoices
            WHERE (? IS NULL OR status = ? COLLATE NOCASE)
              AND (? IS NULL OR vendor_id = ?)
            ORDER BY date(due_date), id
            """,
            (normalized_status, normalized_status, vendor_id, vendor_id),
        ).fetchall()
    invoices = [dict(row) for row in rows]
    return {
        "source_tables": ["invoices"],
        "filters": {"status": normalized_status, "vendor_id": vendor_id},
        "count": len(invoices),
        "invoices": invoices,
    }


@mcp.tool
def get_cash_status(account_name: str | None = None) -> dict[str, Any]:
    """Return recorded cash balances without adding revenue or changing cash."""
    normalized_account = account_name.strip() if account_name is not None else None
    with closing(_connect()) as connection:
        desk = connection.execute(
            "SELECT date_today FROM desk LIMIT 1"
        ).fetchone()
        rows = connection.execute(
            """
            SELECT name, balance, date
            FROM cash_accounts
            WHERE (? IS NULL OR name = ? COLLATE NOCASE)
            ORDER BY name
            """,
            (normalized_account, normalized_account),
        ).fetchall()
    accounts = [dict(row) for row in rows]
    return {
        "source_tables": ["cash_accounts", "desk"],
        "date_today": desk["date_today"] if desk is not None else None,
        "account_name": normalized_account,
        "count": len(accounts),
        "accounts": accounts,
        "total_balance": _rounded_money(
            sum(float(account["balance"]) for account in accounts)
        ),
        "cash_inflows_modeled": False,
    }


@mcp.tool
def get_lease_status(lease_id: int | None = None) -> dict[str, Any]:
    """Return lease and rent timing facts relative to desk.date_today."""
    with closing(_connect()) as connection:
        desk = connection.execute(
            "SELECT date_today FROM desk LIMIT 1"
        ).fetchone()
        if desk is None:
            raise ValueError("The desk table does not contain date_today.")
        rows = connection.execute(
            """
            SELECT id, space_name, landlord, monthly_rent, next_due, notes
            FROM leases
            WHERE (? IS NULL OR id = ?)
            ORDER BY date(next_due), id
            """,
            (lease_id, lease_id),
        ).fetchall()

    today = date.fromisoformat(desk["date_today"])
    leases = []
    for row in rows:
        item = dict(row)
        days_until_due = (date.fromisoformat(item["next_due"]) - today).days
        item["days_until_due"] = days_until_due
        item["is_overdue"] = days_until_due < 0
        leases.append(item)
    return {
        "source_tables": ["leases", "desk"],
        "date_today": desk["date_today"],
        "lease_id": lease_id,
        "count": len(leases),
        "leases": leases,
    }


@mcp.tool
def check_vendor_status(
    vendor_id: int | None = None,
    invoice_id: int | None = None,
    specialty: str | None = None,
) -> dict[str, Any]:
    """Return one vendor's lead time and open invoice, or a short directory.

    Pass vendor_id, invoice_id, or specialty, such as apparel. Without one of
    those, the result lists each vendor's name, specialty, lead time, and open
    invoice count. This tool does not claim that a vendor can supply a SKU
    because the database has no vendor-to-SKU mapping or vendor product costs.
    """
    specialty_filter = specialty.strip() if isinstance(specialty, str) and specialty.strip() else None
    with closing(_connect()) as connection:
        if invoice_id is not None:
            invoice = connection.execute(
                """
                SELECT id, vendor_id, amount, due_date, status, description
                FROM invoices
                WHERE id = ?
                """,
                (invoice_id,),
            ).fetchone()
            if invoice is None:
                raise ValueError(f"Invoice {invoice_id} was not found.")
            derived_vendor_id = invoice["vendor_id"]
            if vendor_id is not None and vendor_id != derived_vendor_id:
                raise ValueError(
                    "The supplied vendor_id conflicts with the invoice vendor."
                )
            vendor_id = derived_vendor_id

        if vendor_id is None and specialty_filter is None:
            directory_rows = connection.execute(
                """
                SELECT id, name, specialty, lead_days
                FROM vendors
                ORDER BY lead_days, id
                """
            ).fetchall()
            directory = []
            for row in directory_rows:
                open_count = connection.execute(
                    """
                    SELECT COUNT(*) AS open_count
                    FROM invoices
                    WHERE vendor_id = ? AND lower(status) = 'open'
                    """,
                    (row["id"],),
                ).fetchone()
                directory.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "specialty": row["specialty"],
                        "lead_days": row["lead_days"],
                        "open_invoice_count": int(open_count["open_count"]),
                    }
                )
            return {
                "source_tables": ["vendors", "invoices"],
                "selection": "directory",
                "vendor_id": None,
                "invoice_id": None,
                "specialty": None,
                "count": len(directory),
                "vendors": directory,
                "sku_eligibility_known": False,
                "vendor_product_cost_known": False,
                "note": "Pass vendor_id or specialty for that vendor's open invoice.",
            }

        vendor_rows = connection.execute(
            """
            SELECT id, name, specialty, lead_days
            FROM vendors
            WHERE (? IS NULL OR id = ?)
              AND (? IS NULL OR specialty LIKE '%' || ? || '%' COLLATE NOCASE)
            ORDER BY lead_days, id
            """,
            (vendor_id, vendor_id, specialty_filter, specialty_filter),
        ).fetchall()

        vendors = []
        for vendor_row in vendor_rows:
            vendor = dict(vendor_row)
            invoice_rows = connection.execute(
                """
                SELECT id, amount, due_date, status, description
                FROM invoices
                WHERE vendor_id = ? AND lower(status) = 'open'
                ORDER BY date(due_date), id
                """,
                (vendor["id"],),
            ).fetchall()
            open_invoices = [dict(row) for row in invoice_rows]
            vendor["open_invoices"] = open_invoices
            vendor["open_invoice_count"] = len(open_invoices)
            vendor["can_ship_new_product_under_shop_rule"] = not open_invoices
            vendors.append(vendor)

    return {
        "source_tables": ["vendors", "invoices"],
        "selection": "vendor",
        "vendor_id": vendor_id,
        "invoice_id": invoice_id,
        "specialty": specialty_filter,
        "count": len(vendors),
        "vendors": vendors,
        "sku_eligibility_known": False,
        "vendor_product_cost_known": False,
    }


def _database_logical_digest(path: Path) -> str:
    with closing(_connect_path(path)) as connection:
        dump = "\n".join(connection.iterdump())
    return hashlib.sha256(dump.encode("utf-8")).hexdigest()


@mcp.tool
def verify_database_reset() -> dict[str, Any]:
    """Verify that the working database exactly matches the original database.

    This is read-only. It does not perform a reset or modify either database.
    """
    original_digest = _database_logical_digest(ORIGINAL_DATABASE_PATH)
    working_digest = _database_logical_digest(DATABASE_PATH)
    return {
        "source_databases": [
            ORIGINAL_DATABASE_PATH.name,
            DATABASE_PATH.name,
        ],
        "original_logical_sha256": original_digest,
        "working_logical_sha256": working_digest,
        "matches_original": original_digest == working_digest,
        "database_mutated": False,
    }


if __name__ == "__main__":
    mcp.run(show_banner=False)
