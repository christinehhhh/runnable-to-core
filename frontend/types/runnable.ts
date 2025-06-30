export type Runnable = {
  id: string
  name: string
  criticality: number
  affinity: number
  period?: number
  execution_time: number
  type: 'periodic' | 'event'
  dependencies: string[]
}

export type SimulationForm = {
  numCores: number
  runnables: Runnable[]
}
