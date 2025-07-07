import { notFound } from 'next/navigation'
import ResultTabs from './ResultTabs'

type ExecutionLogEntry = {
  start: number
  end: number
  task: string
  instance: number
  affinity: number
}

type AlgorithmResult = {
  totalExecutionTime: number
  executionLog: ExecutionLogEntry[]
  ganttChart: string | null
}

type MultiAlgorithmResult = Record<string, AlgorithmResult>

async function getResult(id: string) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'
  const res = await fetch(`${baseUrl}/api/simulate?id=${id}`, {
    cache: 'no-store',
  })
  if (!res.ok) return null
  return res.json()
}

export default async function ResultPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const res = await getResult(id)
  if (!res) return notFound()
  const results: MultiAlgorithmResult = res.results || {
    single: {
      totalExecutionTime: res.totalExecutionTime,
      executionLog: res.executionLog,
      ganttChart: res.ganttChart,
    },
  }
  const availableAlgorithms = res.results
    ? Object.keys(res.results)
    : ['single']

  return (
    <div className="max-w-4xl mx-auto py-10 px-4">
      <h1 className="text-3xl font-bold mb-6">Simulation Result: {id}</h1>
      <ResultTabs availableAlgorithms={availableAlgorithms} results={results} />
    </div>
  )
}
