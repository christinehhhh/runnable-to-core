'use client'
import { RunnableConfig } from '@/types/runnable'
import { useMemo, useState } from 'react'
import { Edge, MarkerType, Node } from 'reactflow'
import 'reactflow/dist/style.css'
import { RunnableConfigPanel, RunnablePlayground } from './_components'

function computeNodeDepths(runnables: RunnableConfig) {
  const depths: Record<string, number> = {}
  const getDepth = (name: string): number => {
    if (depths[name] !== undefined) return depths[name]
    const deps = runnables[name].deps
    if (!deps || deps.length === 0) {
      depths[name] = 0
      return 0
    }
    const d = 1 + Math.max(...deps.map(getDepth))
    depths[name] = d
    return d
  }
  Object.keys(runnables).forEach(getDepth)
  return depths
}

export default function Home() {
  const [runnables, setRunnables] = useState<RunnableConfig>({
    Runnable1: {
      criticality: 0,
      affinity: 0,
      period: 100,
      execution_time: 5,
      type: 'periodic',
      deps: [],
    },
  })

  const nodes: Node[] = useMemo(() => {
    const depths = computeNodeDepths(runnables)
    const levels: string[][] = []
    Object.entries(depths).forEach(([name, depth]) => {
      if (!levels[depth]) levels[depth] = []
      levels[depth].push(name)
    })

    const nodeMap: Record<string, { x: number; y: number }> = {}
    const verticalSpacing = 120
    const horizontalSpacing = 120

    levels.forEach((level, depth) => {
      const y = depth * verticalSpacing
      const totalWidth = (level.length - 1) * horizontalSpacing
      level.forEach((name, i) => {
        const x = i * horizontalSpacing - totalWidth / 2
        nodeMap[name] = { x, y }
      })
    })

    return Object.entries(runnables).map(([name]) => ({
      id: name,
      data: { label: name },
      position: nodeMap[name] || { x: 0, y: 0 },
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
    }))
  }, [runnables])

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
