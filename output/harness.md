# Homework 5 Harness

This harness will expand as the homework progresses. The database reference below describes the tables and fields in `data/campus_customs_new.db`.

## Database reference

### `cash_accounts`

Fields:

- `name` — `TEXT`, primary key
- `balance` — `REAL`, required
- `date` — `TEXT`, required

**Why this table matters for the agents:**
This table contains the checking accounts that agents must use to pay bills, issue customer refunds, and buy inventory, and we must ensure it doesn't fall below zero.

Clarification: The pay tool must check this balance and refuse any payment that would make it negative.

### `desk`

Fields:

- `date_today` — `TEXT`, required
- `notes` — `TEXT`, optional

**Why this table matters for the agents:**
The desk defines what "today" is so the agents have a frame of reference for their requests and queries, since everything is time-sensitive relative to this starting point.

Clarification: Agents must use `desk.date_today` instead of the computer's system date when determining whether something is due or overdue.

### `inventory`

Fields:

- `sku` — `TEXT`, required, part of the composite primary key
- `name` — `TEXT`, required
- `size` — `TEXT`, required, part of the composite primary key
- `qty` — `INTEGER`, required
- `location` — `TEXT`, required

**Why this table matters for the agents:**
Shows what the store has in stock, where it is located, and how much in stock we have so agents can facilitate orders and restocking.

Clarification: The composite key makes each SKU-and-size combination a distinct inventory record.

### `invoices`

Fields:

- `id` — `INTEGER`, primary key
- `vendor_id` — `INTEGER`, required
- `amount` — `REAL`, required
- `due_date` — `TEXT`, required
- `status` — `TEXT`, required
- `description` — `TEXT`, optional

**Why this table matters for the agents:**
Shows accounts receivable / payable / work to be done that agents must consider for payments.

Clarification: In this dataset, invoices represent vendor obligations and accounts payable rather than customer accounts receivable.

### `leases`

Fields:

- `id` — `INTEGER`, primary key
- `space_name` — `TEXT`, required
- `landlord` — `TEXT`, required
- `monthly_rent` — `REAL`, required
- `next_due` — `TEXT`, required
- `notes` — `TEXT`, optional

**Why this table matters for the agents:**
Shows rent payable that agents will have to pay from checking account.

Clarification: Facilities and accounting agents may prepare a rent payment, but only a human may approve it.

### `payments`

Fields:

- `id` — `INTEGER`, primary key
- `kind` — `TEXT`, required
- `ref_id` — `INTEGER`, optional
- `amount` — `REAL`, required
- `account` — `TEXT`, required
- `paid_at` — `TEXT`, required
- `approved_by` — `TEXT`, required

**Why this table matters for the agents:**
currently blank but will eventually contain payments that are ultimately approved by humans.

Clarification: This table records completed payments and their human approver; an agent cannot approve a payment.

### `pricing`

Fields:

- `sku` — `TEXT`, primary key
- `unit_cost` — `REAL`, required
- `list_price` — `REAL`, required

**Why this table matters for the agents:**
Shows the margins we have for each product, use by Accounting agent to track profits.

Clarification: It supports per-unit gross-margin and pricing decisions, although this homework does not model incoming revenue.

### `tickets`

Fields:

- `id` — `INTEGER`, primary key
- `type` — `TEXT`, required
- `requester` — `TEXT`, required
- `subject` — `TEXT`, required
- `sku` — `TEXT`, optional
- `size` — `TEXT`, optional
- `qty` — `INTEGER`, optional
- `lease_id` — `INTEGER`, optional
- `invoice_id` — `INTEGER`, optional
- `status` — `TEXT`, required
- `notes` — `TEXT`, optional
- `created_at` — `TEXT`, required

**Why this table matters for the agents:**
These are the core tickets the homework asks the agents to solve. the boss agent will call these, then delegate and make decisions. 

Clarification: The ticket status provides the shared workflow state that the team can use to track unresolved and completed work.

### `vendors`

Fields:

- `id` — `INTEGER`, primary key
- `name` — `TEXT`, required
- `specialty` — `TEXT`, required
- `lead_days` — `INTEGER`, required

**Why this table matters for the agents:**
contains lead times agents will need for restocking items, agents must use this to ensure inventory is restocked on time.

Clarification: Agents must use each vendor's stored specialty and `lead_days` rather than inventing restocking options or timelines.

## MCP tools

### `check_inventory_status`

- **Reads:** `tickets`, `inventory`
- **Flexible inputs:** Accepts a ticket ID or direct SKU/size; an optional requested quantity enables shortfall calculations. A sized request returns that size only. Omitting size returns each size and quantity.
- **Tickets unlocked:** 101 and 103
- **Why this tool fits:** Ticket 101 requests one `CC-TEE-WHITE` in size S, and the database shows zero available, so the tool returns an exact shortfall of one. Ticket 103 requests 20 `CC-HOOD-NAVY` hoodies in size M, and the database shows eight available, so it returns an exact shortfall of 12 without changing stock.

### `check_pricing_and_margin`

- **Reads:** `tickets`, `pricing`
- **Flexible inputs:** Accepts a ticket ID or direct SKU, with optional quantity and proposed unit price; caller-provided prices are labelled and evaluated but never approved.
- **Ticket unlocked:** 103
- **Why this tool fits:** Ticket 103 asks for a bulk-price override, so the tool retrieves the stored $22 unit cost and $58 list price and calculates the 20-unit totals and list-price gross margin. For that ticket type it also returns four proposal prices calculated from those stored numbers: $58, $50, $45, and $40. Each option includes per-unit profit, margin, and the total for 20, and each is marked unapproved. Other ticket types do not receive that list.

### `draft_payment_for_human_review`

- **Reads:** `tickets`, `invoices`, `leases`, `cash_accounts`, `desk`
- **Flexible inputs:** Accepts a ticket, invoice, lease, or payment kind such as `rent`; conflicting selectors are rejected instead of guessed.
- **Ticket unlocked:** 102; it can also review invoice 501 linked to ticket 101
- **Why this tool fits:** Ticket 102 references lease 1, whose $2,400 rent is due September 2 relative to the shop date of August 31; against the $3,400 checking balance, the projected balance is $1,000. The tool returns that proposal for human review while never approving, executing, recording, or deducting a payment.

### `list_open_tickets`

- **Reads:** `tickets`
- **Tickets unlocked:** 101, 102, and 103
- **Why this tool fits:** The Boss needs a database-grounded work queue before assigning tasks. It returns exact ticket records filtered by status and optional type without changing ticket status.

### `list_invoices`

- **Reads:** `invoices`
- **Ticket unlocked:** 101
- **Why this tool fits:** Ticket 101 references invoice 501. This tool lets Accounting and Inventory confirm the exact $840 open invoice due August 28 without inferring invoice facts from ticket notes.

### `get_cash_status`

- **Reads:** `cash_accounts`, `desk`
- **Tickets unlocked:** 101 and 102; it also supports any later purchase-order review for ticket 103
- **Why this tool fits:** Payment and purchase-order proposals must be checked against recorded cash. It returns the $3,400 checking balance and total balance, labels that no inflows are modeled, and never changes cash.

### `get_lease_status`

- **Reads:** `leases`, `desk`
- **Ticket unlocked:** 102
- **Why this tool fits:** It returns lease 1's exact $2,400 monthly rent and September 2 due date, then calculates that it is due in two days using the shop date of August 31 rather than the computer clock.

### `check_vendor_status`

- **Reads:** `vendors`, `invoices`
- **Tickets unlocked:** 101 and 103, subject to a documented data limitation
- **Why this tool fits:** Inventory must use stored vendor lead times and must know whether an open invoice blocks new shipments. Pass a vendor id, invoice id, or specialty to get that vendor and its open invoice. Without a selector, the tool returns a short directory of name, specialty, lead time, and open-invoice count. SKU eligibility and vendor product cost stay unknown because the database has no vendor-to-SKU mapping or vendor cost table.

### `verify_database_reset`

- **Reads:** every table in baseline `campus_customs.db` and working `campus_customs_new.db` through logical database dumps
- **Tickets unlocked:** the full-run gate for 101, 102, and 103
- **Why this tool fits:** Before an all-open-ticket run, the backend compares logical SHA-256 digests and refuses to continue unless the working database exactly matches the baseline. The check is read-only and does not reset either file itself.

## Agent team

All five PydanticAI agents are created in `backend/team.py`. Every agent uses only `gpt-6-luna` through the Portkey Responses endpoint, receives the shared MCP toolset, and has the same `delegate_to_agent` tool. Portkey rewrites a function-call item id to `portkey_cache_…`. Before the follow-up request leaves the shop, that id is rewritten to the `fc` and `call` prefixes Azure requires, and the tool result keeps the same `call` id. The audit still stores the id Portkey returned. This gives every agent connectivity to every other agent while the runtime rejects self-delegation, cycles, duplicate tasks, excessive depth, and excessive total delegation.

### Boss

- **Prompt:** `backend/prompts/boss.md`
- **Role:** On a single ticket, the record is loaded for her without a model call. She does not check the reset or list the other tickets. When a ticket needs stock and a payment, she calls inventory and accounting in the same step. An invoice already on the ticket is a bill for accounting even when a new restock is blocked. If she finishes without that draft, the runtime asks accounting once before the run ends. On a rent notice she calls facilities and accounting together, and the stored rent is drafted even when the due date is still ahead. If she finishes without that rent draft, the runtime asks accounting once before the run ends. On a price override she keeps the restock draft. If that draft is missing and the stored shortfall is greater than zero, with one vendor and no open invoice, the runtime adds the shortfall times the stored unit cost as a purchase for human approval. That addition reads the shop records and does not call the model. A full run still verifies the reset in code before any ticket starts. She reviews the short specialist summaries, keeps their unsent draft and pending amount, and makes the final decision. The person at the desk enters the discount.

### Inventory

- **Prompt:** `backend/prompts/inventory.md`
- **Role:** Checks stock by SKU and size, the shortfall, vendor specialty, lead time, and whether that vendor has an open unpaid invoice. An open invoice is reported so accounting can draft that existing bill. A missing SKU link does not block a restock draft when that vendor has no open invoice. Payment preparation goes to accounting, and customer wording goes to customer service.

### Accounting

- **Prompt:** `backend/prompts/accounting.md`
- **Role:** Reviews cash, invoices, and margins and prepares payment or purchase-order drafts for a human. On a price override, accounting calls pricing once, reports the stored unit cost, list price, and current margin, and drafts the shortfall times the stored unit cost as a restock even when that payment would make cash negative. It does not propose discount prices. The person at the desk enters the discount. A second accounting pass is refused once accounting has already returned. If that return has no restock draft, the runtime adds one from the stored shortfall and unit cost when the vendor has no open invoice. Quantities come from inventory and the lease record comes from facilities. Accounting cannot approve or execute a payment, and does not write the customer note.

### Facilities

- **Prompt:** `backend/prompts/facilities.md`
- **Role:** Reports the lease, landlord, space, rent, and whether it is due, using `desk.date_today`. A rent notice is drafted for human approval even when the due date is still ahead. The rent payment draft goes to accounting.

### Customer Service

- **Prompt:** `backend/prompts/customer_service.md`
- **Role:** Writes one unsent customer note from facts the other agents returned. On a price override, the note describes the shortfall and lead time and does not propose a price. The person enters a per-unit discount in Human approval. The desk refuses a discount greater than the stored current margin. It shows the current margin, that discount, and the margin after the discount in dollars and percent per unit, then adds the resulting quote and order total to the unsent note. A missing fact is requested once from the agent who owns it. The note stays on the board.

## Agent loop and audit trail

- `backend/main.py ticket <id>` asks the Boss to coordinate one ticket.
- `backend/main.py all` first calls `verify_database_reset`, discovers work with `list_open_tickets`, and then coordinates each open ticket.
- Delegated child runs share the parent usage counter so token and request limits apply across the nested team.
- `output/audit_trail.json` is an append-preserved JSON list. Existing valid events are loaded and retained; writes use a temporary file plus atomic replacement. If the file is invalid, the logger refuses to overwrite it.
- Each event includes schema version, timestamp, run and event IDs, agent, event type, loop step, ticket, delegation path details, fixed model name, tool and call IDs, redacted arguments, bounded result summary, status or stop reason, duration, usage, and sanitized error details.
- The audit records tool calls and results, delegation, run boundaries, reset checks, and final-result validation. It does not record hidden reasoning or chain-of-thought.

## Safety and cost controls

- **Human authority:** Agents can draft payment and purchase-order proposals only. No tool approves or executes payments, and no payment can proceed when projected cash is negative.
- **Read-only shop data:** The MCP server opens SQLite in read-only and query-only mode. Agents have no direct SQLite layer, payment writer, inventory mutator, email sender, or vendor-calling tool.
- **External communications:** Customer messages remain unsent board drafts. Vendor outreach and customer email require a separate human-controlled system that is not present here.
- **Grounding and uncertainty:** Shop facts must come from named MCP results. Missing, conflicting, or unsupported data must produce a blocker or user question; tool output is treated as untrusted data rather than instructions.
- **Secrets:** `gpt-6-luna` is hard-coded, the Portkey key is loaded only at runtime, `.env` and key files are git-ignored, and audit/error values are credential-redacted and truncated.
- **Workflow gates:** A full run stops unless the working database matches the baseline. Agent identity and ticket ID in structured outputs are validated before acceptance.
- **Cost limits:** Each root ticket run allows at most 20 model responses, 40,000 total tokens, 30 successful tool calls, eight delegations, three delegation levels, one retry, and 180 seconds. Nested runs share these budgets. Each model call receives the role paragraph, the role boundary, and the shop rules once. Each specialist is offered only that role's tools and returns a short report with status, summary, and an optional pending amount, price list, or unsent draft. A sized stock check returns that size, and a named vendor check returns that vendor. Older tool payloads become one line that keeps the quantities, amounts, and vendor. The audit keeps the full record.
- **Production additions:** A real deployment should also add authenticated role-based approvals, two-person approval above a dollar threshold, per-payment limits, idempotency keys, immutable centralized logs, PII retention controls, prompt-injection monitoring, rate limits, alerts, and staged testing before any write or send capability is enabled.

## Backend routes

The dashboard server starts from `backend/` with `uvicorn main:app --reload --port 8000`.

- `GET http://localhost:8000/api/tickets` — returns tickets 101, 102, and 103 and whether each is open or resolved.
- `POST http://localhost:8000/api/tickets/{ticket_id}/run` — runs the agent team on that one ticket and leaves the ticket open.
- `GET http://localhost:8000/api/events` — returns recent agent events, including what each agent reported and which tools they used.
- `POST http://localhost:8000/api/approvals` — records a human-approved invoice, rent, or restock payment and reduces the checking balance. It marks the ticket resolved unless the request says another decision is still open.
- `POST http://localhost:8000/api/tickets/{ticket_id}/decision` — records a human decision that does not move cash, such as a pricing note. It marks the ticket resolved unless the request says another decision is still open.
- `POST http://localhost:8000/api/tickets/{ticket_id}/decline` — records that a person declined the prepared payment or note. Checking does not change. It marks the ticket resolved unless the request says another decision is still open.
- `GET http://localhost:8000/api/cash` — returns the current checking balance from `cash_accounts`.
- `POST http://localhost:8000/api/reset` — restores `campus_customs_new.db` to the original values in `campus_customs.db`.