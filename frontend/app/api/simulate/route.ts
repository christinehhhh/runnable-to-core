import { Runnable } from '@/types/runnable'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const data = await req.json()
  try {
    const backendRes = await fetch('http://localhost:5001/api/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        runnables: Object.fromEntries(
          data.runnables.map((r: Runnable) => [
            r.name,
            { ...r, deps: r.dependencies },
          ])
        ),
        numCores: data.numCores,
        simulationTime: 400,
      }),
    })
    const backendData = await backendRes.json()
    const resultId = Math.random().toString(36).substring(2, 10)
    return NextResponse.json({ resultId, ...backendData })
  } catch (e) {
    return NextResponse.json(
      { error: 'Failed to connect to backend', details: String(e) },
      { status: 500 }
    )
  }
}
