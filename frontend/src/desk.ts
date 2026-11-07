import type { AgentId, AuditEvent, PayKind, SpeechLine, Ticket } from "./types.ts"
import type { ApprovalRequest } from "./types.ts"

export const AGENTS: {
  id: AgentId
  label: string
  character: string
  job: string
  x: number
  y: number
  pitch: number
}[] = [
  { id: "boss", label: "Boss", character: "Boss", job: "Leads the desk and hands out the work", x: 50, y: 28, pitch: 392 },
  { id: "inventory", label: "Inventory", character: "Inventory", job: "Checks stock and shortfalls", x: 18, y: 68, pitch: 523 },
  { id: "accounting", label: "Accounting", character: "Accounting", job: "Prepares payments and watches cash", x: 38, y: 84, pitch: 330 },
  { id: "facilities", label: "Facilities", character: "Facilities", job: "Looks after the shop and the rent", x: 62, y: 84, pitch: 294 },
  { id: "customer_service", label: "Customer Service", character: "Customer Service", job: "Writes unsent notes to customers", x: 80, y: 68, pitch: 659 },
]

const AGENT_IDS = new Set(AGENTS.map((agent) => agent.id))

export function asAgent(value: string | null | undefined): AgentId | null {
  if (value && AGENT_IDS.has(value as AgentId)) return value as AgentId
  return null
}

export function agentMeta(id: AgentId) {
  return AGENTS.find((agent) => agent.id === id) ?? AGENTS[0]
}

export function money(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value)
}

export function percent(value: number): string {
  return `${value.toFixed(2)}%`
}

function cents(value: number): number {
  return Math.round(value * 100) / 100
}

export type UnitQuote = {
  discount: number
  discountPercent: number
  currentMargin: number
  currentPercent: number
  quote: number
  netMargin: number
  netPercent: number
  orderTotal: number
}

export function readDiscount(text: string): number | null {
  const trimmed = text.trim()
  if (!trimmed) return null
  const value = Number(trimmed)
  if (!Number.isFinite(value) || value < 0) return null
  return cents(value)
}

export function currentMargin(listPrice: number, unitCost: number): number {
  return cents(listPrice - unitCost)
}

export function unitQuote(listPrice: number, unitCost: number, discount: number, quantity: number): UnitQuote | null {
  if (listPrice <= 0) return null
  const margin = currentMargin(listPrice, unitCost)
  if (discount > margin) return null
  const quote = cents(listPrice - discount)
  if (quote <= 0) return null
  const netMargin = cents(quote - unitCost)
  return {
    discount,
    discountPercent: cents((discount / listPrice) * 100),
    currentMargin: margin,
    currentPercent: cents((margin / listPrice) * 100),
    quote,
    netMargin,
    netPercent: cents((netMargin / quote) * 100),
    orderTotal: cents(quote * quantity),
  }
}

function clip(value: string | null | undefined, limit = 140): string {
  if (!value) return ""
  const text = value.replace(/\s+/g, " ").trim()
  return text.length <= limit ? text : `${text.slice(0, limit - 1)}…`
}

export function insight(event: AuditEvent): string {
  const speaker = agentMeta(event.agent_name).label
  const tool = event.tool_name?.replaceAll("_", " ")
  switch (event.event_type) {
    case "agent_run_started":
      return `${speaker} is taking a look.`
    case "tool_call_started":
      return tool ? `Using ${tool}.` : "Checking the shop records."
    case "tool_call_completed":
      return tool ? `Finished checking ${tool}.` : "The shop records came back."
    case "delegation_started":
      return event.delegated_to
        ? `Calling ${agentMeta(event.delegated_to).label} over.`
        : "Calling a teammate over."
    case "delegation_completed":
      return event.delegated_to
        ? `Heard back from ${agentMeta(event.delegated_to).label}.`
        : "Heard back from a teammate."
    case "delegation_rejected":
      return clip(event.result_summary) || "That handoff did not go through."
    case "agent_run_completed":
      return clip(event.result_summary) || `${speaker} is finished.`
    case "agent_run_failed":
      return `${speaker} could not continue.`
    default:
      return ""
  }
}

export function toLine(event: AuditEvent): SpeechLine | null {
  const text = insight(event)
  if (!text) return null
  return { id: event.event_id, agent: event.agent_name, text }
}

export type PayAction = {
  kind: PayKind
  label: string
  summary: string
  amount: number | null
}

export function approvedLabel(kind: PayKind): string {
  if (kind === "invoice") return "Invoice payment approved"
  if (kind === "rent") return "Rent payment approved"
  return "Restock purchase approved"
}

export function payActions(ticket: Ticket, requests: ApprovalRequest[]): PayAction[] {
  const actions: PayAction[] = []
  const seen = new Set<PayKind>()
  for (const request of requests) {
    const text = request.summary.toLowerCase()
    let kind: PayKind | null = null
    if (request.kind === "purchase_order" || text.includes("restock")) {
      kind = "restock"
    } else if (request.kind === "payment") {
      if (text.includes("rent") || text.includes("lease")) kind = "rent"
      else if (ticket.invoice_id && !text.includes("restock")) kind = "invoice"
      else if (ticket.lease_id) kind = "rent"
    }
    if (!kind || seen.has(kind)) continue
    seen.add(kind)
    const label =
      kind === "invoice"
        ? "Approve invoice payment"
        : kind === "rent"
          ? "Approve rent payment"
          : "Approve restock purchase"
    actions.push({ kind, label, summary: request.summary, amount: request.amount })
  }
  return actions
}
