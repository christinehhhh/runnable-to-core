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
import { useEffect, useMemo, useState } from 'react'
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

interface DependencySelectorProps {
  allRunnables: string[]
  selected: string[]
  onChange: (deps: string[]) => void
}

const DependencySelector = ({
  allRunnables,
  selected,
  onChange,
}: DependencySelectorProps) => {
  const [search, setSearch] = useState('')
  const [focused, setFocused] = useState(false)
  const filtered = allRunnables.filter(
    (n) =>
      n.toLowerCase().includes(search.toLowerCase()) && !selected.includes(n)
  )

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-1 mb-1">
        {selected.map((dep) => (
          <span
            key={dep}
            className="inline-flex items-center bg-indigo-100 text-indigo-800 rounded px-2 py-0.5 text-xs mr-1"
          >
            {dep}
            <button
              type="button"
              className="ml-1 text-indigo-500 hover:text-red-500"
              onClick={() => onChange(selected.filter((d) => d !== dep))}
              aria-label={`Remove ${dep}`}
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <input
        type="text"
        className="w-full border rounded px-2 py-1 text-sm"
        placeholder="Search and add dependencies..."
        value={search}
        onFocus={() => setFocused(true)}
        onBlur={() => setTimeout(() => setFocused(false), 100)}
        onChange={(e) => setSearch(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && filtered.length > 0) {
            onChange([...selected, filtered[0]])
            setSearch('')
            e.preventDefault()
          }
        }}
      />
      {focused && filtered.length > 0 && (
        <div className="absolute left-0 right-0 border rounded bg-white shadow mt-1 max-h-32 overflow-y-auto z-10">
          {filtered.map((n) => (
            <div
              key={n}
              className="px-2 py-1 cursor-pointer hover:bg-indigo-100"
              onMouseDown={() => {
                onChange([...selected, n])
                setSearch('')
              }}
            >
              {n}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function EditableRunnableName({
  name,
  onRename,
}: {
  name: string
  onRename: (newName: string) => void
}) {
  const [localName, setLocalName] = useState(name)
  useEffect(() => {
    setLocalName(name)
  }, [name])

  return (
    <TextField.Root
      value={localName}
      onChange={(e) => setLocalName(e.target.value)}
      onBlur={() => {
        if (localName !== name && localName.trim() !== '') {
          onRename(localName.trim())
        } else {
          setLocalName(name)
        }
      }}
      onKeyDown={(e) => {
        if (
          e.key === 'Enter' &&
          localName !== name &&
          localName.trim() !== ''
        ) {
          onRename(localName.trim())
        }
      }}
      className="font-semibold w-48"
    />
  )
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
              {Object.entries(runnables)
                .reverse()
                .map(([name, runnable]) => {
                  return (
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
                        <EditableRunnableName
                          name={name}
                          onRename={(newName) =>
                            handleNameChange(name, newName)
                          }
                        />
                      </Flex>
                      <Flex gap="3" wrap="wrap">
                        <Box>
                          <Text size="2">Criticality</Text>
                          <Select.Root
                            value={runnable.criticality.toString()}
                            onValueChange={(value) =>
                              handleRunnableChange(
                                name,
                                'criticality',
                                Number(value)
                              )
                            }
                          >
                            <Select.Trigger className="w-24" />
                            <Select.Content>
                              <Select.Item value="0">0 - ASIL A</Select.Item>
                              <Select.Item value="1">1 - ASIL B</Select.Item>
                              <Select.Item value="2">2 - ASIL C</Select.Item>
                              <Select.Item value="3">3 - ASIL D</Select.Item>
                            </Select.Content>
                          </Select.Root>
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
                              <Select.Item value="periodic">
                                Periodic
                              </Select.Item>
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
                          <Text size="2">Dependencies</Text>
                          <DependencySelector
                            allRunnables={Object.keys(runnables).filter(
                              (n) => n !== name
                            )}
                            selected={runnable.deps}
                            onChange={(deps) =>
                              handleRunnableChange(name, 'deps', deps)
                            }
                          />
                        </Box>
                      </Flex>
                    </Box>
                  )
                })}
            </Flex>
          </Box>
        </ScrollArea>
      </div>
    </div>
  )
}
