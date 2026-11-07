import type { ApprovalResult, Cash, PayKind, TeamRun, Ticket } from "./types.ts"
import type { AuditEvent } from "./types.ts"

export const API_ORIGIN = "http://localhost:8000"

type EventPage = {
  count: number
  total_count: number
  events: AuditEvent[]
}

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === "string") return body.detail
  } catch {
    return "The shop server could not finish that request."
  }
  return "The shop server could not finish that request."
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ORIGIN}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  })
  if (!response.ok) throw new Error(await readError(response))
  return (await response.json()) as T
}

export function getTickets(): Promise<{ count: number; tickets: Ticket[] }> {
  return request("/api/tickets")
}

export function getCash(): Promise<Cash> {
  return request("/api/cash")
}

export function getEvents(): Promise<EventPage> {
  return request("/api/events?limit=200")
}

export function runTicket(ticketId: number): Promise<TeamRun> {
  return request(`/api/tickets/${ticketId}/run`, { method: "POST", body: "{}" })
}

export function resetShop(): Promise<{ reset: boolean; checking_balance: number }> {
  return request("/api/reset", { method: "POST" })
}

export function declineTicket(
  ticketId: number,
  approvedBy: string,
  finishReview = true,
): Promise<{ ticket_state: string }> {
  return request(`/api/tickets/${ticketId}/decline`, {
    method: "POST",
    body: JSON.stringify({ approved_by: approvedBy, finish_review: finishReview }),
  })
}

export function recordDecision(
  ticketId: number,
  approvedBy: string,
  finishReview = true,
): Promise<{ ticket_state: string }> {
  return request(`/api/tickets/${ticketId}/decision`, {
    method: "POST",
    body: JSON.stringify({ approved_by: approvedBy, finish_review: finishReview }),
  })
}

export function approvePayment(
  ticketId: number,
  kind: PayKind,
  approvedBy: string,
  finishReview = true,
): Promise<ApprovalResult> {
  return request("/api/approvals", {
    method: "POST",
    body: JSON.stringify({
      ticket_id: ticketId,
      kind,
      approved_by: approvedBy,
      finish_review: finishReview,
    }),
  })
}
