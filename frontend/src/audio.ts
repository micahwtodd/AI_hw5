import { agentMeta } from "./desk.ts"
import type { AgentId } from "./types.ts"

export function createDeskAudio() {
  let context: AudioContext | null = null
  let muted = false

  function tone(frequency: number, duration: number, when: number) {
    if (!context || muted) return
    const oscillator = context.createOscillator()
    const gain = context.createGain()
    oscillator.type = "sine"
    oscillator.frequency.setValueAtTime(frequency, when)
    gain.gain.setValueAtTime(0.0001, when)
    gain.gain.exponentialRampToValueAtTime(0.05, when + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, when + duration)
    oscillator.connect(gain)
    gain.connect(context.destination)
    oscillator.start(when)
    oscillator.stop(when + duration + 0.02)
  }

  return {
    unlock() {
      if (!context) context = new AudioContext()
      if (context.state === "suspended") void context.resume()
    },
    setMuted(next: boolean) {
      muted = next
    },
    speak(agent: AgentId) {
      if (!context || muted) return
      const now = context.currentTime
      tone(agentMeta(agent).pitch, 0.16, now)
    },
    connect(from: AgentId, to: AgentId) {
      if (!context || muted) return
      const now = context.currentTime
      tone(agentMeta(from).pitch, 0.1, now)
      tone(agentMeta(to).pitch, 0.14, now + 0.11)
    },
  }
}
