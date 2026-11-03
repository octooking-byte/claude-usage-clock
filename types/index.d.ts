export type Limit = { kind: string; percent: number; resetsAt?: string }
export type Meter = { limits: Limit[]; contextTokens?: number; contextWindow: number }
export type Turn = { total: number; fresh: number; requests: number; subRequests: number }

declare module 'claude-code' {
  interface PluginState {
    'token-panel': {
      meter: Shaped<Meter>
      current: Shaped<Turn>
      last: Shaped<Turn>
    }
  }
}
