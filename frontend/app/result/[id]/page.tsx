import { notFound } from 'next/navigation'

type ExecutionLogEntry = {
  start: number
  end: number
  task: string
  instance: number
  affinity: number
}

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
  params: { id: string }
}) {
  const result = await getResult(params.id)
  if (!result) return notFound()

  return (
    <div className="max-w-4xl mx-auto py-10 px-4">
      <h1 className="text-3xl font-bold mb-6">
        Simulation Result: {params.id}
      </h1>
      <div className="mb-6">
        <div className="border-b mb-4">
          <nav className="flex gap-4">
            <span className="py-2 px-4 border-b-2 border-indigo-500 font-semibold">
              Gantt Chart
            </span>
            {/* Add more tabs for other plots if needed */}
          </nav>
        </div>
        {/* Gantt chart image */}
        {result.ganttChart ? (
          <div className="flex justify-center items-center min-h-[300px] bg-gray-50 border rounded">
            <img
              src={`data:image/png;base64,${result.ganttChart}`}
              alt="Gantt Chart"
              className="max-h-[400px]"
            />
          </div>
        ) : (
          <div className="flex justify-center items-center min-h-[300px] bg-gray-50 border rounded">
            <span className="text-gray-400">No Gantt chart available</span>
          </div>
        )}
      </div>
      <div>
        <h2 className="text-xl font-semibold mb-2">Execution Log</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full border">
            <thead>
              <tr>
                <th className="border px-2 py-1">Start</th>
                <th className="border px-2 py-1">End</th>
                <th className="border px-2 py-1">Task</th>
                <th className="border px-2 py-1">Instance</th>
                <th className="border px-2 py-1">Affinity</th>
              </tr>
            </thead>
            <tbody>
              {result.executionLog && result.executionLog.length > 0 ? (
                (result.executionLog as ExecutionLogEntry[]).map((entry, i) => (
                  <tr key={i}>
                    <td className="border px-2 py-1">{entry.start}</td>
                    <td className="border px-2 py-1">{entry.end}</td>
                    <td className="border px-2 py-1">{entry.task}</td>
                    <td className="border px-2 py-1">{entry.instance}</td>
                    <td className="border px-2 py-1">{entry.affinity}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="border px-2 py-1" colSpan={5}>
                    No execution log available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
