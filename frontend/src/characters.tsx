import type { AgentId } from "./types.ts"

const CAST: Record<AgentId, { file: string; name: string; ghost?: boolean }> = {
  boss: { file: "witch", name: "Witch" },
  inventory: { file: "zombie", name: "Zombie" },
  accounting: { file: "vampire", name: "Vampire" },
  facilities: { file: "frankenstein", name: "Frankenstein" },
  customer_service: { file: "ghost", name: "Ghost", ghost: true },
}

export function Character({ id }: { id: AgentId }) {
  const cast = CAST[id]
  return (
    <div
      className={cast.ghost ? "sprite ghost" : "sprite"}
      role="img"
      aria-label={cast.name}
      style={{ backgroundImage: `url(/characters/${cast.file}.png?v=2)` }}
    />
  )
}
