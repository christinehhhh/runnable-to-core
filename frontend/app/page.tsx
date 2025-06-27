'use client'
import { RunnableConfig } from '@/types/runnable'
import { useMemo, useState } from 'react'
import { Edge, MarkerType, Node } from 'reactflow'
import 'reactflow/dist/style.css'
import { RunnableConfigPanel, RunnablePlayground } from './_components'

const defaultRunnables: RunnableConfig = {
  RadarCapture: {
    criticality: 1,
    affinity: 0,
    period: 75,
    execution_time: 2,
    type: 'periodic',
    deps: [],
  },
  CameraCapture: {
    criticality: 0,
    affinity: 0,
    period: 50,
    execution_time: 7,
    type: 'periodic',
    deps: [],
  },
}

export default function Home() {
  const [runnables, setRunnables] = useState<RunnableConfig>(defaultRunnables)

  const nodes: Node[] = useMemo(
    () =>
      Object.entries(runnables).map(([name], i) => ({
        id: name,
        data: { label: name },
        position: {
          x: 150 * Math.cos((2 * Math.PI * i) / Object.keys(runnables).length),
          y: 150 * Math.sin((2 * Math.PI * i) / Object.keys(runnables).length),
        },
        type: 'default',
        style: {
          width: 60,
          height: 60,
          borderRadius: 30,
          background: '#fff',
          border: '2px solid #6366f1',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        },
      })),
    [runnables]
  )
  const edges: Edge[] = useMemo(
    () =>
      Object.entries(runnables).flatMap(([name, r]) =>
        r.deps.map((dep) => ({
          id: `${dep}->${name}`,
          source: dep,
          target: name,
          animated: true,
          style: { stroke: '#6366f1' },
          markerEnd: { type: MarkerType.ArrowClosed },
        }))
      ),
    [runnables]
  )

  return (
    <div className="flex flex-col md:flex-row gap-8 max-w-6xl mx-auto py-10 px-4 min-h-screen h-screen overflow-hidden">
      <RunnablePlayground nodes={nodes} edges={edges} />
      <RunnableConfigPanel runnables={runnables} setRunnables={setRunnables} />
    </div>
  )
}
