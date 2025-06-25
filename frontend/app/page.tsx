'use client'
import { Cross2Icon } from '@radix-ui/react-icons'
import {
  Box,
  Button,
  Flex,
  Heading,
  IconButton,
  ScrollArea,
  Select,
  Text,
  TextField,
} from '@radix-ui/themes'
import { useMemo, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  Edge,
  MarkerType,
  Node,
} from 'reactflow'
import 'reactflow/dist/style.css'

type Runnable = {
  criticality: number
  affinity: number
  period?: number
  execution_time: number
  type: 'periodic' | 'event'
  deps: string[]
}

type RunnableConfig = Record<string, Runnable>

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
  const [numCores, setNumCores] = useState(1)
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

  const handleAddRunnable = () => {
    const newName = `Runnable${Object.keys(runnables).length + 1}`
    setRunnables({
      ...runnables,
      [newName]: {
        criticality: 0,
        affinity: 0,
        period: 100,
        execution_time: 5,
        type: 'periodic',
        deps: [],
      },
    })
  }

  const handleRemoveRunnable = (name: string) => {
    const newRunnables = { ...runnables }
    delete newRunnables[name]
    Object.keys(newRunnables).forEach((k) => {
      newRunnables[k].deps = newRunnables[k].deps.filter((dep) => dep !== name)
    })
    setRunnables(newRunnables)
  }

  const handleRunnableChange = (
    name: string,
    field: keyof Runnable,
    value: number | string | string[] | 'periodic' | 'event'
  ) => {
    setRunnables((prev) => ({
      ...prev,
      [name]: {
        ...prev[name],
        [field]: value,
      },
    }))
  }

  const handleNameChange = (oldName: string, newName: string) => {
    if (!newName || oldName === newName) return
    setRunnables((prev) => {
      const updated = { ...prev }
      updated[newName] = updated[oldName]
      delete updated[oldName]
      Object.keys(updated).forEach((k) => {
        updated[k].deps = updated[k].deps.map((dep) =>
          dep === oldName ? newName : dep
        )
      })
      return updated
    })
  }

  return (
    <div className="flex flex-col md:flex-row gap-8 max-w-6xl mx-auto py-10 px-4 min-h-screen h-screen overflow-hidden">
      <div className="flex-1 bg-white rounded-lg shadow-md p-4 min-h-[500px] flex items-center justify-center">
        <div style={{ width: '100%', height: 500 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
            zoomOnScroll={false}
            panOnScroll
          >
            <Background />
            <Controls />
          </ReactFlow>
        </div>
      </div>
      <div className="w-full md:w-[400px]">
        <ScrollArea scrollbars="vertical">
          <Heading className="text-2xl font-bold mb-6 text-center">
            Configuration
          </Heading>
          <Box mb="5">
            <Text as="label" size="3" className="block mb-2 font-medium">
              Number of Cores
            </Text>
            <TextField.Root
              type="number"
              min={1}
              max={16}
              value={numCores}
              onChange={(e) => setNumCores(Number(e.target.value) || 1)}
              className="w-32"
            />
          </Box>
          <Box mb="5">
            <Flex justify="between" align="center" mb="2">
              <Text as="label" size="3" className="font-medium">
                Runnables
              </Text>
              <Button variant="soft" onClick={handleAddRunnable}>
                Add Runnable
              </Button>
            </Flex>
            <Flex direction="column" gap="4">
              {Object.entries(runnables).map(([name, runnable]) => (
                <Box
                  key={name}
                  className="border rounded-lg p-4 bg-gray-50 relative"
                >
                  <IconButton
                    variant="ghost"
                    color="red"
                    className="absolute top-2 right-2"
                    onClick={() => handleRemoveRunnable(name)}
                    aria-label="Remove Runnable"
                  >
                    <Cross2Icon />
                  </IconButton>
                  <Flex gap="2" align="center" mb="2">
                    <TextField.Root
                      value={name}
                      onChange={(e) => handleNameChange(name, e.target.value)}
                      className="font-semibold w-48"
                    />
                  </Flex>
                  <Flex gap="3" wrap="wrap">
                    <Box>
                      <Text size="2">Criticality</Text>
                      <TextField.Root
                        type="number"
                        min={0}
                        max={3}
                        value={runnable.criticality}
                        onChange={(e) =>
                          handleRunnableChange(
                            name,
                            'criticality',
                            Number(e.target.value) || 0
                          )
                        }
                        className="w-20"
                      />
                    </Box>
                    <Box>
                      <Text size="2">Affinity</Text>
                      <TextField.Root
                        type="number"
                        min={0}
                        max={numCores - 1}
                        value={runnable.affinity}
                        onChange={(e) =>
                          handleRunnableChange(
                            name,
                            'affinity',
                            Number(e.target.value) || 0
                          )
                        }
                        className="w-20"
                      />
                    </Box>
                    <Box>
                      <Text size="2">Execution Time (ms)</Text>
                      <TextField.Root
                        type="number"
                        min={1}
                        value={runnable.execution_time}
                        onChange={(e) =>
                          handleRunnableChange(
                            name,
                            'execution_time',
                            Number(e.target.value) || 1
                          )
                        }
                        className="w-24"
                      />
                    </Box>
                    <Box>
                      <Text size="2">Type</Text>
                      <Select.Root
                        value={runnable.type}
                        onValueChange={(value) =>
                          handleRunnableChange(
                            name,
                            'type',
                            value as 'periodic' | 'event'
                          )
                        }
                      >
                        <Select.Trigger className="w-28" />
                        <Select.Content>
                          <Select.Item value="periodic">Periodic</Select.Item>
                          <Select.Item value="event">Event</Select.Item>
                        </Select.Content>
                      </Select.Root>
                    </Box>
                    {runnable.type === 'periodic' && (
                      <Box>
                        <Text size="2">Period (ms)</Text>
                        <TextField.Root
                          type="number"
                          min={1}
                          value={runnable.period || 100}
                          onChange={(e) =>
                            handleRunnableChange(
                              name,
                              'period',
                              Number(e.target.value) || 100
                            )
                          }
                          className="w-24"
                        />
                      </Box>
                    )}
                    <Box className="flex-1 min-w-[180px]">
                      <Text size="2">Dependencies (comma separated)</Text>
                      <TextField.Root
                        value={runnable.deps.join(', ')}
                        onChange={(e) =>
                          handleRunnableChange(
                            name,
                            'deps',
                            e.target.value
                              .split(',')
                              .map((d) => d.trim())
                              .filter((d) => d)
                          )
                        }
                        placeholder="e.g. RadarCapture, CameraCapture"
                      />
                    </Box>
                  </Flex>
                </Box>
              ))}
            </Flex>
          </Box>
        </ScrollArea>
      </div>
    </div>
  )
}
