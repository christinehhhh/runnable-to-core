'use client'
import { Cross2Icon } from '@radix-ui/react-icons'
import {
  Box,
  Button,
  Flex,
  Heading,
  IconButton,
  Select,
  Text,
  TextField,
} from '@radix-ui/themes'
import { useState } from 'react'

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
      return updated
    })
  }

  return (
    <div className="max-w-3xl mx-auto py-10 px-4">
      <Heading className="text-2xl font-bold mb-6 text-center">
        Scheduling Simulator Config
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
                <InputBox
                  title="Execution Time (ms)"
                  type="number"
                  value={runnable.execution_time}
                  onChange={(e) =>
                    handleRunnableChange(
                      name,
                      'execution_time',
                      Number(e.target.value) || 1
                    )
                  }
                />
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
                  <InputBox
                    title="Period (ms)"
                    type="number"
                    value={runnable.period || 100}
                    onChange={(e) =>
                      handleRunnableChange(
                        name,
                        'period',
                        Number(e.target.value) || 100
                      )
                    }
                  />
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
    </div>
  )
}

interface InputBoxProps {
  title: string
  type: 'text' | 'number'
  value: string | number
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

const InputBox = ({ title, type, value, onChange }: InputBoxProps) => {
  return (
    <Box>
      <Text size="2">{title}</Text>
      <TextField.Root type={type} value={value} onChange={onChange} />
    </Box>
  )
}
