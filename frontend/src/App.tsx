import { useEffect, useRef, useState } from "react"
import { approvePayment, declineTicket, getCash, getEvents, getTickets, recordDecision, resetShop, runTicket } from "./api.ts"
import { createDeskAudio } from "./audio.ts"
import { Character } from "./characters.tsx"
import { AGENTS, agentMeta, approvedLabel, asAgent, currentMargin, money, payActions, percent, readDiscount, toLine, unitQuote } from "./desk.ts"
import type { AgentId, AgentReport, Cash, PayKind, SpeechLine, TalkLink, Ticket } from "./types.ts"

const ORG_LINKS = AGENTS.filter((agent) => agent.id !== "boss").map((agent) => ({
  from: "boss" as const,
  to: agent.id,
}))

const DESK_MEMORY = "campus-customs-desk-v2"

type TicketDesk = {
  lines: SpeechLine[]
  summaries: Partial<Record<AgentId, string>>
  report: AgentReport | null
  bubbles: Partial<Record<AgentId, string>>
  links: TalkLink[]
}

function emptyDesk(): TicketDesk {
  return { lines: [], summaries: {}, report: null, bubbles: {}, links: [] }
}

export default function App() {
  const audio = useRef(createDeskAudio())
  const seenEvents = useRef(new Set<string>())
  const pollRef = useRef<number | null>(null)
  const thinkingRef = useRef<AgentId[]>([])
  const thinkGeneration = useRef<Partial<Record<AgentId, number>>>({})
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [cash, setCash] = useState<Cash | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [runningId, setRunningId] = useState<number | null>(null)
  const [boards, setBoards] = useState<Record<number, TicketDesk>>({})
  const [liveAgents, setLiveAgents] = useState<AgentId[]>([])
  const [thinking, setThinking] = useState<AgentId[]>([])

  useEffect(() => {
    thinkingRef.current = thinking
  }, [thinking])
  const [soundOn, setSoundOn] = useState(true)
  const [motionOn, setMotionOn] = useState(() => !window.matchMedia("(prefers-reduced-motion: reduce)").matches)
  const [transcriptOpen, setTranscriptOpen] = useState(false)
  const [approver, setApprover] = useState("")
  const [discountDrafts, setDiscountDrafts] = useState<Record<number, string>>({})
  const [discountBlockedId, setDiscountBlockedId] = useState<number | null>(null)
  const [cashNote, setCashNote] = useState("")
  const [message, setMessage] = useState("")
  const [approvedKeys, setApprovedKeys] = useState<Record<string, true>>({})
  const [declinedKeys, setDeclinedKeys] = useState<Record<string, true>>({})
  const [pendingKey, setPendingKey] = useState<string | null>(null)
  const approving = useRef(false)
  const [loadError, setLoadError] = useState("")
  const [memoryReady, setMemoryReady] = useState(false)

  const selected = tickets.find((ticket) => ticket.id === selectedId) ?? null
  const desk = selectedId != null ? boards[selectedId] ?? null : null
  const lines = desk?.lines ?? []
  const summaries = desk?.summaries ?? {}
  const report = desk?.report ?? null
  const bubbles = desk?.bubbles ?? {}
  const links = desk?.links ?? []
  const viewingRun = runningId !== null && runningId === selectedId
  const reportedCount = AGENTS.filter((agent) => summaries[agent.id]).length
  const workingLabels = [...new Set([...thinking, ...liveAgents])].map((id) => agentMeta(id).label)
  const runStatus = statusLine(viewingRun, reportedCount, viewingRun ? workingLabels : [])

  function updateDesk(ticketId: number, change: (desk: TicketDesk) => TicketDesk) {
    setBoards((current) => {
      const existing = current[ticketId] ?? emptyDesk()
      return { ...current, [ticketId]: change(existing) }
    })
  }

  function actionsFor(ticket: Ticket | null) {
    if (!ticket) return []
    const ticketReport = boards[ticket.id]?.report
    if (!ticketReport || ticketReport.ticket_id !== ticket.id) return []
    return payActions(ticket, ticketReport.approval_requests)
  }

  const actions = actionsFor(selected)
  const needsYouId = tickets.find((ticket) => ticket.state !== "resolved" && actionsFor(ticket).length > 0)?.id ?? null

  useEffect(() => {
    const raw = sessionStorage.getItem(DESK_MEMORY)
    if (raw) {
      try {
        const saved = JSON.parse(raw) as {
          selectedId?: number
          boards?: Record<number, TicketDesk>
          lines?: SpeechLine[]
          summaries?: Partial<Record<AgentId, string>>
          report?: AgentReport | null
        }
        if (saved.selectedId) setSelectedId(saved.selectedId)
        if (saved.boards) {
          setBoards(saved.boards)
        } else if (saved.selectedId && (saved.lines || saved.summaries || saved.report)) {
          setBoards({
            [saved.selectedId]: {
              lines: saved.lines ?? [],
              summaries: saved.summaries ?? {},
              report: saved.report ?? null,
              bubbles: {},
              links: [],
            },
          })
        }
      } catch {
        sessionStorage.removeItem(DESK_MEMORY)
      }
    }
    setMemoryReady(true)
  }, [])

  useEffect(() => {
    if (!memoryReady) return
    sessionStorage.setItem(
      DESK_MEMORY,
      JSON.stringify({ selectedId, boards }),
    )
  }, [memoryReady, selectedId, boards])

  useEffect(() => {
    let cancel = false
    async function load() {
      try {
        const [ticketPage, cashPage] = await Promise.all([getTickets(), getCash()])
        if (cancel) return
        setTickets(ticketPage.tickets)
        setCash(cashPage)
        setLoadError("")
      } catch {
        if (!cancel) setLoadError("The desk cannot reach the shop server at http://localhost:8000.")
      }
    }
    void load()
    const timer = window.setInterval(() => void load(), 15000)
    return () => {
      cancel = true
      window.clearInterval(timer)
      if (pollRef.current) window.clearInterval(pollRef.current)
    }
  }, [])

  function toggleSound() {
    const next = !soundOn
    setSoundOn(next)
    audio.current.setMuted(!next)
    if (next) audio.current.unlock()
  }

  async function refreshShop() {
    const [ticketPage, cashPage] = await Promise.all([getTickets(), getCash()])
    setTickets(ticketPage.tickets)
    setCash(cashPage)
  }

  function absorb(events: Parameters<typeof toLine>[0][], ticketId: number) {
    const freshLines: SpeechLine[] = []
    for (const event of events) {
      if (!asAgent(event.agent_name)) continue
      const line = toLine(event)
      if (line) freshLines.push(line)
      if (event.event_type === "delegation_started" && event.delegated_to) {
        audio.current.connect(event.agent_name, event.delegated_to)
      } else if (event.event_type === "agent_run_started" || event.event_type === "agent_run_completed") {
        audio.current.speak(event.agent_name)
      }
    }
    const revealed = freshLines.filter((line) => {
      const event = events.find((item) => item.event_id === line.id)
      return event ? !["agent_run_started", "tool_call_started"].includes(event.event_type) : true
    })
    if (revealed.length) {
      updateDesk(ticketId, (current) => ({
        ...current,
        lines: [...current.lines, ...revealed].slice(-60),
      }))
    }

    const wasThinking = new Set(thinkingRef.current)
    const started = new Set<AgentId>()
    for (const event of events) {
      if (!asAgent(event.agent_name)) continue
      if (event.event_type === "agent_run_started" || event.event_type === "tool_call_started") {
        started.add(event.agent_name)
      }
      if (event.event_type === "delegation_started") {
        if (event.delegated_to) started.add(event.delegated_to)
        const handoff = toLine(event)
        if (handoff) {
          updateDesk(ticketId, (current) => ({
            ...current,
            bubbles: { ...current.bubbles, [event.agent_name]: handoff.text },
          }))
        }
      }
    }
    if (started.size) {
      for (const agent of started) thinkGeneration.current[agent] = (thinkGeneration.current[agent] ?? 0) + 1
      setThinking((current) => [...new Set([...current, ...started])])
    }
    for (const event of events) {
      if (
        event.event_type !== "tool_call_completed" &&
        event.event_type !== "delegation_completed" &&
        event.event_type !== "delegation_rejected" &&
        event.event_type !== "agent_run_completed" &&
        event.event_type !== "agent_run_failed"
      ) {
        continue
      }
      const line = toLine(event)
      if (!line) continue
      const agent = event.agent_name
      const generation = (thinkGeneration.current[agent] ?? 0) + 1
      thinkGeneration.current[agent] = generation
      const delay = started.has(agent) || !wasThinking.has(agent)
      if (delay) setThinking((current) => (current.includes(agent) ? current : [...current, agent]))
      window.setTimeout(() => {
        if (thinkGeneration.current[agent] !== generation) return
        updateDesk(ticketId, (current) => ({
          ...current,
          bubbles: { ...current.bubbles, [agent]: line.text },
        }))
        setThinking((current) => current.filter((name) => name !== agent))
      }, delay ? 700 : 0)
    }

    updateDesk(ticketId, (current) => {
      const summaries = { ...current.summaries }
      for (const event of events) {
        if (event.event_type === "agent_run_completed" && event.result_summary) {
          summaries[event.agent_name] = event.result_summary
        }
      }
      return { ...current, summaries }
    })
    setLiveAgents((current) => {
      const next = new Set(current)
      for (const event of events) {
        if (event.event_type === "agent_run_started" || event.event_type === "delegation_started") {
          next.add(event.agent_name)
          if (event.delegated_to) next.add(event.delegated_to)
        }
        if (event.event_type === "agent_run_completed" || event.event_type === "agent_run_failed") {
          next.delete(event.agent_name)
        }
        if (event.event_type === "delegation_completed" || event.event_type === "delegation_rejected") {
          if (event.delegated_to) next.delete(event.delegated_to)
        }
      }
      return [...next]
    })
    updateDesk(ticketId, (current) => {
      const next = [...current.links]
      for (const event of events) {
        if (!event.delegated_to) continue
        const id = event.tool_call_id || event.event_id
        const index = next.findIndex((link) => link.id === id)
        const live = event.event_type === "delegation_started"
        if (event.event_type !== "delegation_started" && event.event_type !== "delegation_completed" && event.event_type !== "delegation_rejected") {
          continue
        }
        const link = { id, from: event.agent_name, to: event.delegated_to, live }
        if (index >= 0) next[index] = link
        else next.push(link)
      }
      return { ...current, links: next }
    })
  }

  async function pullEvents(ticketId: number) {
    const page = await getEvents()
    const fresh = page.events.filter(
      (event) => event.ticket_id === ticketId && !seenEvents.current.has(event.event_id),
    )
    for (const event of fresh) seenEvents.current.add(event.event_id)
    if (fresh.length) absorb(fresh, ticketId)
  }

  async function startTeam() {
    if (!selected || runningId) return
    audio.current.unlock()
    audio.current.setMuted(!soundOn)
    const ticketId = selected.id
    setRunningId(ticketId)
    updateDesk(ticketId, () => emptyDesk())
    setLiveAgents(["boss"])
    setThinking(["boss"])
    setCashNote("")
    setMessage("")
    try {
      const prior = await getEvents()
      seenEvents.current = new Set(prior.events.map((event) => event.event_id))
      pollRef.current = window.setInterval(() => {
        void pullEvents(ticketId).catch(() => undefined)
      }, 1000)
      const result = await runTicket(ticketId)
      await pullEvents(ticketId)
      updateDesk(ticketId, (current) => ({
        ...current,
        report: result.report,
        summaries: result.report.summary
          ? { ...current.summaries, boss: result.report.summary }
          : current.summaries,
      }))
      await refreshShop()
      setMessage(
        result.ticket_ready
          ? `The team has finished ticket ${ticketId}. It stays open until you take action.`
          : `Ticket ${ticketId} is still open. The invoice payment was not prepared.`,
      )
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The team could not finish this ticket.")
    } finally {
      if (pollRef.current) window.clearInterval(pollRef.current)
      pollRef.current = null
      setRunningId(null)
      setLiveAgents([])
      setThinking([])
      updateDesk(ticketId, (current) => ({
        ...current,
        links: current.links.map((link) => ({ ...link, live: false })),
      }))
    }
  }

  async function resetDesk() {
    if (!window.confirm("Reset the shop database to its original values?")) return
    try {
      const result = await resetShop()
      setBoards({})
      setDiscountDrafts({})
      setDiscountBlockedId(null)
      setLiveAgents([])
      setThinking([])
      setApprovedKeys({})
      setDeclinedKeys({})
      setPendingKey(null)
      approving.current = false
      setCashNote("")
      setMessage(`Shop reset. Checking is ${money(result.checking_balance)}.`)
      await refreshShop()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The shop could not be reset.")
    }
  }

  async function approve(kind: PayKind) {
    if (!selected || approving.current) return
    const key = `${selected.id}:${kind}`
    if (approvedKeys[key]) return
    const name = approver.trim()
    if (!name) {
      setMessage("Add your name before approving a payment.")
      return
    }
    approving.current = true
    setPendingKey(key)
    try {
      const finish = reviewFinishes("payment", kind)
      const result = await approvePayment(selected.id, kind, name, finish)
      setApprovedKeys((current) => ({ ...current, [key]: true }))
      setCash({ account: "checking", balance: result.balance_after, date: cash?.date ?? "" })
      setCashNote(`Checking moved from ${money(result.balance_before)} to ${money(result.balance_after)}.`)
      setMessage(
        finish
          ? `${result.kind} approved for ${money(result.amount)}. Ticket ${selected.id} is resolved.`
          : `${result.kind} approved for ${money(result.amount)}. The price decision is still waiting.`,
      )
      await refreshShop()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The payment was not approved.")
    } finally {
      approving.current = false
      setPendingKey(null)
    }
  }

  async function decline(kind: PayKind | "note") {
    if (!selected || approving.current) return
    const key = `${selected.id}:${kind}`
    if (approvedKeys[key] || declinedKeys[key] || selected.state === "resolved") return
    const name = approver.trim()
    if (!name) {
      setMessage(kind === "note" ? "Add your name before declining." : "Add your name before declining a payment.")
      return
    }
    approving.current = true
    setPendingKey(`${key}:decline`)
    try {
      const finish = reviewFinishes(kind === "note" ? "note" : "payment", kind === "note" ? undefined : kind)
      await declineTicket(selected.id, name, finish)
      setDeclinedKeys((current) => ({ ...current, [key]: true }))
      const decided = kind === "note" ? "Decision declined" : "Payment declined"
      setMessage(
        finish
          ? `${decided}. Checking did not change. Ticket ${selected.id} is resolved.`
          : `${decided}. Checking did not change. The other decision is still waiting.`,
      )
      await refreshShop()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The payment was not declined.")
    } finally {
      approving.current = false
      setPendingKey(null)
    }
  }

  async function recordNote() {
    if (!selected || approving.current) return
    const name = approver.trim()
    if (!name) {
      setMessage("Add your name before recording a decision.")
      return
    }
    if (selected.type === "price_override" && !quote) {
      const margin = selected.list_price != null && selected.unit_cost != null
        ? currentMargin(selected.list_price, selected.unit_cost)
        : null
      setMessage(
        discountAmount != null && margin != null && discountAmount > margin
          ? `The discount cannot be greater than the current margin of ${money(margin)} per unit.`
          : "Enter a discount per unit before recording the quote.",
      )
      return
    }
    approving.current = true
    setPendingKey(`${selected.id}:decision`)
    try {
      const finish = reviewFinishes("note")
      await recordDecision(selected.id, name, finish)
      setApprovedKeys((current) => ({ ...current, [`${selected.id}:note`]: true }))
      setMessage(
        finish
          ? `Decision recorded. Ticket ${selected.id} is resolved. Checking did not change.`
          : "Decision recorded. Checking did not change. The payment decision is still waiting.",
      )
      await refreshShop()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The decision was not recorded.")
    } finally {
      approving.current = false
      setPendingKey(null)
    }
  }

  const priceQuote = selected?.type === "price_override" && report?.ticket_id === selected.id
  const notes = (report?.approval_requests ?? []).filter((request) => {
    if (priceQuote && request.kind === "discount") return false
    return request.kind === "discount" || request.kind === "other"
  })
  const customerDraft = report?.drafts.find((draft) => !draft.sent) ?? report?.drafts[0]
  const discountText = selected ? discountDrafts[selected.id] ?? "" : ""
  const discountAmount = readDiscount(discountText)
  const marginCap = selected && selected.list_price != null && selected.unit_cost != null
    ? currentMargin(selected.list_price, selected.unit_cost)
    : null
  const discountOverMargin = discountAmount != null && marginCap != null && discountAmount > marginCap
  const quote = selected && selected.list_price != null && selected.unit_cost != null && discountAmount != null
    ? unitQuote(selected.list_price, selected.unit_cost, discountAmount, selected.qty ?? 1)
    : null
  const quoteLine = quote && selected
    ? `Final quote for ${selected.qty ?? 1}${selected.size ? ` size ${selected.size}` : ""} ${selected.sku ?? "items"}: ${money(quote.quote)} per unit, the ${money(selected.list_price ?? 0)} list price less a ${money(quote.discount)} discount. The order total is ${money(quote.orderTotal)}. Margin after the discount is ${money(quote.netMargin)} per unit (${percent(quote.netPercent)}).`
    : ""

  function reviewFinishes(closing: "payment" | "note", kind?: PayKind): boolean {
    if (!selected) return true
    const paymentLeft = actions.some((action) => {
      if (closing === "payment" && action.kind === kind) return false
      const actionKey = `${selected.id}:${action.kind}`
      return !approvedKeys[actionKey] && !declinedKeys[actionKey]
    })
    const noteKey = `${selected.id}:note`
    const quoteLeft = Boolean(priceQuote && closing !== "note" && !approvedKeys[noteKey] && !declinedKeys[noteKey])
    const noteLeft = quoteLeft || (notes.length > 0 && closing !== "note" && !approvedKeys[noteKey] && !declinedKeys[noteKey])
    return !paymentLeft && !noteLeft
  }

  return (
    <div className={motionOn ? "desk" : "desk still"}>
      <header className="top">
        <div className="brand">
          <span className="mark">CC</span>
          <div>
            <strong>Campus Customs</strong>
            <small>Operations desk</small>
          </div>
        </div>
        <div className={`cash ${cashNote ? "dropped" : ""}`}>
          <span>Checking</span>
          <strong>{cash ? money(cash.balance) : "—"}</strong>
          <small>{cash ? `Shop date ${cash.date}` : "Waiting for the server"}</small>
          {cashNote ? <em>{cashNote}</em> : null}
        </div>
        <div className="header-actions">
          <button type="button" className="quiet" onClick={() => void resetDesk()} disabled={runningId !== null}>
            Reset shop
          </button>
          <button type="button" className="quiet" onClick={toggleSound} aria-pressed={soundOn}>
            {soundOn ? "Sound on" : "Sound off"}
          </button>
          <button type="button" className="quiet" onClick={() => setMotionOn((current) => !current)} aria-pressed={motionOn}>
            {motionOn ? "Motion on" : "Motion off"}
          </button>
        </div>
      </header>

      <div className="board">
      {loadError || message ? (
        <div className="notice" role="status">
          <div>
            {loadError ? <p>{loadError}</p> : null}
            {message ? <p>{message}</p> : null}
          </div>
          <button
            type="button"
            className="notice-close"
            aria-label="Dismiss notice"
            onClick={() => {
              setMessage("")
              setLoadError("")
            }}
          >
            ×
          </button>
        </div>
      ) : null}
      <section className="tickets" aria-label="Tickets">
        {tickets.map((ticket) => (
          <button
            key={ticket.id}
            type="button"
            className={["ticket", ticket.id === selectedId ? "selected" : "", ticket.id === needsYouId ? "needs-you" : ""].filter(Boolean).join(" ")}
            onClick={() => setSelectedId(ticket.id)}
            aria-pressed={ticket.id === selectedId}
          >
            <span className="pills">
              {ticket.state === "resolved" ? (
                <span className="pill reviewed">Human Review Complete</span>
              ) : ticket.id === needsYouId ? (
                <span className="pill needs">Needs you</span>
              ) : null}
              <span className={ticket.state === "resolved" ? "pill resolved" : "pill"}>{ticket.state}</span>
            </span>
            <strong>Ticket {ticket.id}</strong>
            <em>{ticket.subject}</em>
            <small>{ticket.requester}</small>
          </button>
        ))}
      </section>

      <div className="work">
        <section className="floor-wrap">
          <div className="floor-head">
            <div>
              <h1>{selected ? selected.subject : "Choose a ticket"}</h1>
              <p>
                {selected
                  ? `${selected.requester} · ${selected.type.replaceAll("_", " ")}`
                  : "The three open tickets are listed above. Pick one to wake the team."}
              </p>
              {runStatus ? <p className="run-status" role="status">{runStatus}</p> : null}
            </div>
            <button type="button" className="primary" disabled={!selected || runningId !== null} onClick={() => void startTeam()}>
              {runningId ? `Working on ${runningId}` : "Start the team"}
            </button>
          </div>

          <div className="floor" aria-label="Agent team">
            <div className="haunt" aria-hidden="true">
              <span className="moon" />
              <span className="star one" />
              <span className="star two" />
              <span className="star three" />
              <span className="star four" />
              <span className="web" />
              <span className="lantern left" />
              <span className="lantern right" />
            </div>
            <svg className="links" viewBox="0 0 100 100" preserveAspectRatio="none">
              {ORG_LINKS.map((link) => (
                <Connection key={`${link.from}-${link.to}`} from={link.from} to={link.to} mode="org" />
              ))}
              {links.map((link) => (
                <Connection key={link.id} from={link.from} to={link.to} mode={link.live ? "talking" : "talked"} />
              ))}
            </svg>
            {AGENTS.map((agent) => {
              const live = viewingRun && liveAgents.includes(agent.id)
              const bubble = bubbles[agent.id]
              const waiting = viewingRun && thinking.includes(agent.id)
              return (
                <article key={agent.id} className={agent.id === "boss" ? "station boss" : "station"} style={{ left: `${agent.x}%`, top: `${agent.y}%` }}>
                  {waiting ? (
                    <p className="bubble thinking" aria-label="Thinking">
                      <span />
                      <span />
                      <span />
                    </p>
                  ) : bubble ? (
                    <p className="bubble">{bubble}</p>
                  ) : null}
                  {agent.id === "boss" ? (
                    <div className="nameplate">
                      <strong><RoleMark id={agent.id} />{agent.label}</strong>
                      <small>{agent.job}</small>
                    </div>
                  ) : null}
                  <div className={live ? "figure live" : "figure"}>
                    <Character id={agent.id} />
                  </div>
                  {agent.id === "boss" ? null : (
                    <div className="nameplate">
                      <strong><RoleMark id={agent.id} />{agent.label}</strong>
                      <small>{agent.job}</small>
                    </div>
                  )}
                </article>
              )
            })}
          </div>
          <p className="legend">When two people talk, a new line appears between them. A pumpkin and a piece of candy travel that line.</p>
          <section className="email-card" aria-label="Unsent customer email">
            <h2>Unsent customer email</h2>
            {customerDraft ? (
              <>
                <p className="summary"><strong>To</strong><span>{customerDraft.audience}</span></p>
                <p className="summary"><strong>Subject</strong><span>{customerDraft.subject}</span></p>
                <p>{customerDraft.body}{quoteLine ? ` ${quoteLine}` : ""}</p>
                <p className="hint">This email was not sent.</p>
              </>
            ) : (
              <p className="empty">No customer email yet.</p>
            )}
          </section>
        </section>

        <aside>
          <section className="approval-card">
            <h2>Human approval</h2>
            <p className="hint">The team can prepare a payment. Checking changes only when you approve it.</p>
            <label>
              Your name
              <input value={approver} onChange={(event) => setApprover(event.target.value)} placeholder="Who is approving" />
            </label>
            {actions.length === 0 ? <p className="empty">No payment is waiting.</p> : null}
            {actions.map((action) => (
              <div key={action.kind} className="approval">
                <p>{action.summary}</p>
                {action.amount != null && cash ? (
                  <small>Prepared amount {money(action.amount)}. The desk pays the stored database amount.</small>
                ) : null}
                <div className="decision-row">
                  <button
                    type="button"
                    disabled={Boolean(selected && (selected.state === "resolved" || approvedKeys[`${selected.id}:${action.kind}`] || declinedKeys[`${selected.id}:${action.kind}`] || pendingKey))}
                    onClick={() => void approve(action.kind)}
                  >
                    <span>
                      {selected && approvedKeys[`${selected.id}:${action.kind}`]
                        ? approvedLabel(action.kind)
                        : pendingKey === `${selected?.id}:${action.kind}`
                          ? "Approving…"
                          : action.label}
                    </span>
                    <small>
                      {selected && approvedKeys[`${selected.id}:${action.kind}`]
                        ? "This payment is already recorded."
                        : consequence(cash?.balance ?? null, action.amount)}
                    </small>
                  </button>
                  <button
                    type="button"
                    className="decline"
                    disabled={Boolean(selected && (selected.state === "resolved" || approvedKeys[`${selected.id}:${action.kind}`] || declinedKeys[`${selected.id}:${action.kind}`] || pendingKey))}
                    onClick={() => void decline(action.kind)}
                  >
                    <span>
                      {selected && declinedKeys[`${selected.id}:${action.kind}`]
                        ? "Payment declined"
                        : pendingKey === `${selected?.id}:${action.kind}:decline`
                          ? "Declining…"
                          : "Decline"}
                    </span>
                    <small>
                      {selected && declinedKeys[`${selected.id}:${action.kind}`]
                        ? "Checking did not change."
                        : "Leave this unpaid. Checking stays the same."}
                    </small>
                  </button>
                </div>
              </div>
            ))}
            {priceQuote && selected && selected.list_price != null && selected.unit_cost != null ? (
              <div className="approval">
                <p>Enter the discount per unit. It cannot be greater than the current margin of {money(selected.list_price - selected.unit_cost)}. The stored list price is {money(selected.list_price)} and the stored unit cost is {money(selected.unit_cost)}.</p>
                <table className="margin-table">
                  <thead>
                    <tr>
                      <th>Item</th>
                      <th>Dollars per unit</th>
                      <th>Percent</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <th scope="row">Current margin</th>
                      <td>{money(selected.list_price - selected.unit_cost)}</td>
                      <td>{percent(((selected.list_price - selected.unit_cost) / selected.list_price) * 100)}</td>
                    </tr>
                    <tr>
                      <th scope="row">Discount</th>
                      <td>
                        <input
                          aria-label="Discount per unit in dollars"
                          aria-invalid={discountOverMargin || discountBlockedId === selected.id}
                          inputMode="decimal"
                          value={discountText}
                          placeholder="0.00"
                          onChange={(event) => {
                            const value = event.target.value
                            const amount = readDiscount(value)
                            const margin = currentMargin(selected.list_price ?? 0, selected.unit_cost ?? 0)
                            if (amount != null && amount > margin) {
                              setDiscountBlockedId(selected.id)
                              return
                            }
                            setDiscountBlockedId((current) => current === selected.id ? null : current)
                            setDiscountDrafts((current) => ({ ...current, [selected.id]: value }))
                          }}
                        />
                      </td>
                      <td>{quote ? percent(quote.discountPercent) : "—"}</td>
                    </tr>
                    <tr>
                      <th scope="row">Margin after discount</th>
                      <td>{quote ? money(quote.netMargin) : "—"}</td>
                      <td>{quote ? percent(quote.netPercent) : "—"}</td>
                    </tr>
                  </tbody>
                </table>
                {discountText.trim() && discountAmount == null ? <p className="hint">Enter a discount of zero or more dollars per unit.</p> : null}
                {discountOverMargin || discountBlockedId === selected.id ? <p className="hint">The discount cannot be greater than the current margin of {money(marginCap ?? 0)} per unit.</p> : null}
                {discountAmount != null && !discountOverMargin && !quote ? <p className="hint">This discount uses up the list price, so there is no quote yet.</p> : null}
                <div className="decision-row">
                    <button
                      type="button"
                      disabled={Boolean(selected.state === "resolved" || approvedKeys[`${selected.id}:note`] || declinedKeys[`${selected.id}:note`] || pendingKey || !quote)}
                      onClick={() => void recordNote()}
                    >
                      <span>{pendingKey === `${selected.id}:decision` ? "Recording…" : approvedKeys[`${selected.id}:note`] ? "Quote recorded" : "Record this quote"}</span>
                      <small>Checking stays the same.</small>
                    </button>
                    <button
                      type="button"
                      className="decline"
                      disabled={Boolean(selected.state === "resolved" || approvedKeys[`${selected.id}:note`] || declinedKeys[`${selected.id}:note`] || pendingKey)}
                      onClick={() => void decline("note")}
                    >
                      <span>
                        {declinedKeys[`${selected.id}:note`]
                          ? "Quote declined"
                          : pendingKey === `${selected.id}:note:decline`
                            ? "Declining…"
                            : "Decline"}
                      </span>
                      <small>Leave the quote unaccepted. Checking stays the same.</small>
                    </button>
                  </div>
              </div>
            ) : null}
            {notes.map((note) => (
              <div key={note.summary} className="approval">
                <p>{note.summary} This note does not change cash.</p>
                <div className="decision-row">
                    <button
                      type="button"
                      disabled={Boolean(selected && (selected.state === "resolved" || approvedKeys[`${selected.id}:note`] || declinedKeys[`${selected.id}:note`] || pendingKey))}
                      onClick={() => void recordNote()}
                    >
                      <span>{pendingKey === `${selected?.id}:decision` ? "Recording…" : selected && approvedKeys[`${selected.id}:note`] ? "Decision recorded" : "Record this decision"}</span>
                      <small>Checking stays the same.</small>
                    </button>
                    <button
                      type="button"
                      className="decline"
                      disabled={Boolean(selected && (selected.state === "resolved" || approvedKeys[`${selected.id}:note`] || declinedKeys[`${selected.id}:note`] || pendingKey))}
                      onClick={() => void decline("note")}
                    >
                      <span>
                        {selected && declinedKeys[`${selected.id}:note`]
                          ? "Decision declined"
                          : pendingKey === `${selected?.id}:note:decline`
                            ? "Declining…"
                            : "Decline"}
                      </span>
                      <small>Leave the note unaccepted. Checking stays the same.</small>
                    </button>
                  </div>
              </div>
            ))}
          </section>

          <section>
            <h2>Conversation</h2>
            <button type="button" className="transcript-toggle" onClick={() => setTranscriptOpen((current) => !current)} aria-expanded={transcriptOpen}>
              {transcriptOpen ? "Hide the transcript" : `Show the transcript${lines.length ? ` (${lines.length})` : ""}`}
            </button>
            {transcriptOpen ? (
              <div className="log" aria-live="polite">
                {lines.length === 0 ? <p className="empty">Speech shows up here once the team starts.</p> : null}
                {lines.map((line) => (
                  <p key={line.id} className="log-line">
                    <strong>{agentMeta(line.agent).character}</strong>
                    <span>{line.text}</span>
                  </p>
                ))}
              </div>
            ) : (
              <p className="hint">The floor shows the latest line. Open the transcript for the full exchange.</p>
            )}
          </section>

          <section>
            <h2>What each agent did</h2>
            {AGENTS.map((agent) => (
              <p key={agent.id} className="summary">
                <strong>{agent.character}</strong>
                <span>{summaries[agent.id] || "No summary yet."}</span>
              </p>
            ))}
          </section>
        </aside>
      </div>
      </div>
    </div>
  )
}

function statusLine(running: boolean, reported: number, working: string[]): string {
  const total = AGENTS.length
  if (running) {
    const who = working.length === 0
      ? "The team is working"
      : working.length === 1
        ? `${working[0]} is working`
        : `${working.join(" and ")} are working`
    return `${who}. ${reported} of ${total} have reported.`
  }
  if (reported === total) return `The team has finished. ${reported} of ${total} have reported.`
  if (reported > 0) return `The team is idle. ${reported} of ${total} have reported.`
  return ""
}

function consequence(balance: number | null, amount: number | null): string {
  if (balance == null || amount == null) return "Checking changes by the stored amount."
  const next = Math.round((balance - amount) * 100) / 100
  return `Pay ${money(amount)}. Checking becomes ${money(next)}.`
}

function RoleMark({ id }: { id: AgentId }) {
  return (
    <svg className="role-mark" viewBox="0 0 16 16" aria-hidden="true">
      {id === "boss" ? (
        <g fill="currentColor">
          <path d="M1.5 7.2 8.1 3.1c.5-.3 1.1-.1 1.4.4l1.3 2.2c.3.5.1 1.1-.4 1.4L3.8 11c-.5.3-1.1.1-1.4-.4L1.1 8.4c-.3-.5-.1-1.1.4-1.2z" />
          <path d="M7.4 8.8 12.9 14.2c.35.35.95.35 1.3 0l.55-.55c.35-.35.35-.95 0-1.3L9.2 7l-1.8 1.8z" />
        </g>
      ) : null}
      {id === "inventory" ? (
        <g fill="none" stroke="currentColor" strokeWidth="1.35" strokeLinejoin="round">
          <path d="M1.8 6.1 8 3 14.2 6.1 V11.6 L8 14.7 1.8 11.6 Z" />
          <path d="M1.8 6.1 8 9.2 14.2 6.1" />
          <path d="M8 9.2 V14.7" />
        </g>
      ) : null}
      {id === "accounting" ? (
        <path
          fill="currentColor"
          fillRule="evenodd"
          d="M3 1.4h10v13.2H3z M4.5 2.8h7v2.5h-7z M4.6 6.4h2v1.7h-2z M7 6.4h2v1.7H7z M9.4 6.4h2v1.7h-2z M4.6 8.8h2v1.7h-2z M7 8.8h2v1.7H7z M9.4 8.8h2v1.7h-2z M4.6 11.2h2v1.7h-2z M7 11.2h4.4v1.7H7z"
        />
      ) : null}
      {id === "facilities" ? (
        <path
          fill="currentColor"
          d="M10.7 1.2a3.3 3.3 0 0 0-2.5 4.3L3.1 10.6a1.45 1.45 0 0 0 0 2.05l.85.85a1.45 1.45 0 0 0 2.05 0l5.1-5.1A3.3 3.3 0 0 0 14.8 6L12.4 8.4 10.2 6.2 12.6 3.8A3.3 3.3 0 0 0 10.7 1.2z"
        />
      ) : null}
      {id === "customer_service" ? (
        <g fill="none" stroke="currentColor" strokeWidth="1.35" strokeLinecap="round">
          <circle cx="8" cy="8" r="6.2" />
          <circle cx="5.6" cy="6.7" r="0.7" fill="currentColor" stroke="none" />
          <circle cx="10.4" cy="6.7" r="0.7" fill="currentColor" stroke="none" />
          <path d="M5.1 9.3c.9 1.7 4.9 1.7 5.8 0" />
        </g>
      ) : null}
    </svg>
  )
}

function curve(x1: number, y1: number, x2: number, y2: number, bend: number) {
  const dx = x2 - x1
  const dy = y2 - y1
  const length = Math.hypot(dx, dy) || 1
  const cx = (x1 + x2) / 2 + (-dy / length) * bend
  const cy = (y1 + y2) / 2 + (dx / length) * bend
  return `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`
}

function Connection({ from, to, mode }: { from: AgentId; to: AgentId; mode: "org" | "talking" | "talked" }) {
  const start = agentMeta(from)
  const end = agentMeta(to)
  const side = end.x > start.x ? -1 : 1
  const bend = (mode === "org" ? 4 : 14) * side
  const path = curve(start.x, start.y, end.x, end.y, bend)
  const talking = mode === "talking"
  return (
    <g>
      <path d={path} pathLength={100} className={mode === "org" ? "link" : talking ? "link talk" : "link talked"} vectorEffect="non-scaling-stroke" />
      {talking ? (
        <>
          <Treat path={path} kind="pumpkin" begin="0s" />
          <Treat path={path} kind="candy" begin="-1.7s" />
        </>
      ) : null}
    </g>
  )
}

function Treat({ path, kind, begin }: { path: string; kind: "pumpkin" | "candy"; begin: string }) {
  return (
    <g className="treat">
      {kind === "pumpkin" ? <Pumpkin /> : <Candy />}
      <animateMotion
        dur="3.4s"
        begin={begin}
        repeatCount="indefinite"
        calcMode="linear"
        keyPoints="0;1;0"
        keyTimes="0;0.5;1"
        path={path}
      />
    </g>
  )
}

function Pumpkin() {
  return (
    <g>
      <ellipse cx="0" cy="0.2" rx="3.1" ry="2.35" fill="#e85d04" />
      <ellipse cx="-1.05" cy="0.2" rx="0.95" ry="2.15" fill="#f48c06" />
      <ellipse cx="1.05" cy="0.2" rx="0.95" ry="2.15" fill="#dc2f02" />
      <path d="M-0.05 -1.9 q0.2 -1.2 1.15 -0.7" fill="none" stroke="#386641" strokeWidth="0.45" strokeLinecap="round" />
    </g>
  )
}

function Candy() {
  return (
    <g>
      <path d="M-3.1 0 L-1.7 -1 v2 Z" fill="#9b2226" />
      <path d="M3.1 0 L1.7 -1 v2 Z" fill="#9b2226" />
      <rect x="-1.7" y="-0.75" width="3.4" height="1.5" rx="0.16" fill="#fff3bf" />
      <path d="M-0.5 -0.75 v1.5 M0.5 -0.75 v1.5" stroke="#e85d04" strokeWidth="0.22" />
    </g>
  )
}
