export type Runnable = {
  name: string
  criticality: number
  affinity: number
  period?: number
  execution_time: number
  type: 'periodic' | 'event'
  dependencies: string[]
}
