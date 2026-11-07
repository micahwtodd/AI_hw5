"""Shared structured types for the Campus Customs agent team."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from threading import Lock
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentName(StrEnum):
    BOSS = "boss"
    INVENTORY = "inventory"
    ACCOUNTING = "accounting"
    FACILITIES = "facilities"
    CUSTOMER_SERVICE = "customer_service"


class TaskStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    NEEDS_HUMAN_APPROVAL = "needs_human_approval"
    NEEDS_CLARIFICATION = "needs_clarification"


@dataclass
class DelegationState:
    """Mutable limits shared by a root run and every delegated child run."""

    max_depth: int = 3
    max_delegations: int = 8
    total_delegations: int = 0
    seen_tasks: set[str] = field(default_factory=set)
    specialist_reports: list[Any] = field(default_factory=list)
    lock: Any = field(default_factory=Lock, repr=False)


@dataclass
class TeamDeps:
    """Runtime context available to one agent and its delegation tool."""

    run_id: str
    ticket_id: int | None
    current_agent: AgentName
    delegation_depth: int
    delegation_path: tuple[AgentName, ...]
    delegation_state: DelegationState
    ticket_brief: str = ""


class Evidence(BaseModel):
    """One factual statement grounded in a named MCP tool result."""

    statement: str
    source_tool: str
    source_tables: list[str] = Field(default_factory=list)


class HumanApprovalRequest(BaseModel):
    """A proposal that cannot proceed without an actual human decision."""

    kind: Literal["payment", "purchase_order", "discount", "other"]
    summary: str
    amount: float | None = None
    reference_id: int | str | None = None
    status: Literal["pending_human_review"] = "pending_human_review"


class DraftMessage(BaseModel):
    """An unsent communication that remains on the operations board."""

    audience: str
    subject: str
    body: str
    ticket_id: int | None = None
    status: Literal["draft"] = "draft"
    sent: Literal[False] = False


class AgentReport(BaseModel):
    """Board report. The model fills the smaller ShortReport, which is expanded here."""

    agent: AgentName
    ticket_id: int | None = None
    status: TaskStatus
    summary: str
    evidence: list[Evidence] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    approval_requests: list[HumanApprovalRequest] = Field(default_factory=list)
    drafts: list[DraftMessage] = Field(default_factory=list)
    questions_for_user: list[str] = Field(default_factory=list)


class PendingAmount(BaseModel):
    """One payment or purchase still waiting for a human."""

    kind: Literal["payment", "purchase_order", "discount", "other"]
    summary: str
    amount: float | None = None


class UnsentNote(BaseModel):
    """One customer note that stays on the board."""

    audience: str
    subject: str
    body: str


class ShortReport(BaseModel):
    """The report the model returns on every call."""

    agent: AgentName
    ticket_id: int | None = None
    status: TaskStatus
    summary: str
    pending: PendingAmount | None = None
    discount: PendingAmount | None = None
    draft: UnsentNote | None = None


def to_board_report(short: ShortReport) -> AgentReport:
    """Expand the model report into the board's approval and draft lists."""
    approvals: list[HumanApprovalRequest] = []
    if short.pending is not None:
        approvals.append(
            HumanApprovalRequest(
                kind=short.pending.kind,
                summary=short.pending.summary,
                amount=short.pending.amount,
            )
        )
    if short.discount is not None:
        approvals.append(
            HumanApprovalRequest(
                kind="discount",
                summary=short.discount.summary,
                amount=short.discount.amount,
            )
        )
    drafts: list[DraftMessage] = []
    if short.draft is not None:
        drafts.append(
            DraftMessage(
                audience=short.draft.audience,
                subject=short.draft.subject,
                body=short.draft.body,
                ticket_id=short.ticket_id,
            )
        )
    return AgentReport(
        agent=short.agent,
        ticket_id=short.ticket_id,
        status=short.status,
        summary=short.summary,
        approval_requests=approvals,
        drafts=drafts,
    )


class AuditEvent(BaseModel):
    """One append-preserved event from an agent run or delegation."""

    schema_version: int = 1
    timestamp: str
    run_id: str
    event_id: str
    agent_name: AgentName
    event_type: str
    loop_step: int
    ticket_id: int | None = None
    delegated_by: AgentName | None = None
    delegated_to: AgentName | None = None
    delegation_depth: int = 0
    model: str = "gpt-6-luna"
    tool_name: str | None = None
    tool_call_id: str | None = None
    tool_arguments: dict[str, Any] | str | None = None
    result_summary: str | None = None
    status: str | None = None
    stop_reason: str | None = None
    duration_ms: int | None = None
    usage: dict[str, Any] | None = None
    error_type: str | None = None
    error_message: str | None = None


class TeamRunResult(BaseModel):
    """Top-level result returned by the Boss orchestration run."""

    run_id: str
    report: AgentReport
    usage: dict[str, Any] = Field(default_factory=dict)
    audit_path: str = "output/audit_trail.json"
    ticket_ready: bool = False
