export type AgentId =
  | "boss"
  | "inventory"
  | "accounting"
  | "facilities"
  | "customer_service"

export type TicketState = "open" | "resolved"

export type Ticket = {
  id: number
  type: string
  requester: string
  subject: string
  sku: string | null
  size: string | null
  qty: number | null
  lease_id: number | null
  invoice_id: number | null
  status: string
  state: TicketState
  notes: string | null
  unit_cost?: number | null
  list_price?: number | null
}

export type Cash = {
  account: string
  balance: number
  date: string
}

export type AuditEvent = {
  event_id: string
  timestamp: string
  agent_name: AgentId
  event_type: string
  ticket_id: number | null
  delegated_by: AgentId | null
  delegated_to: AgentId | null
  tool_name: string | null
  tool_call_id: string | null
  result_summary: string | null
  status: string | null
  error_message: string | null
}

export type ApprovalKind = "payment" | "purchase_order" | "discount" | "other"
export type PayKind = "invoice" | "rent" | "restock"

export type ApprovalRequest = {
  kind: ApprovalKind
  summary: string
  amount: number | null
  reference_id: number | string | null
  status: string
}

export type DraftMessage = {
  audience: string
  subject: string
  body: string
  status: string
  sent: boolean
}

export type AgentReport = {
  agent: AgentId
  ticket_id: number | null
  status: string
  summary: string
  recommendations: string[]
  approval_requests: ApprovalRequest[]
  drafts: DraftMessage[]
  questions_for_user: string[]
}

export type TeamRun = {
  run_id: string
  report: AgentReport
  ticket_state?: string
  ticket_ready?: boolean
}

export type ApprovalResult = {
  approved: boolean
  kind: PayKind
  amount: number
  balance_before: number
  balance_after: number
  description?: string
  quantity?: number
  unit_cost?: number
  vendor_name?: string
  ticket_state?: string
}

export type SpeechLine = {
  id: string
  agent: AgentId
  text: string
}

export type TalkLink = {
  id: string
  from: AgentId
  to: AgentId
  live: boolean
}
