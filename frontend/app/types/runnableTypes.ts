export type Runnable = {
  criticality: number
  affinity: number
  period?: number
  execution_time: number
  type: 'periodic' | 'event'
  deps: string[]
}

export type RunnableConfig = Record<string, Runnable>
