import { Runnable } from '@/types/runnable'
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
import { useEffect, useState } from 'react'

interface Props {
  runnables: Runnable[]
  setRunnables: React.Dispatch<React.SetStateAction<Runnable[]>>
}

const RunnableConfigPanel = ({ runnables, setRunnables }: Props) => {
  const [numCores, setNumCores] = useState(1)

  const handleAddRunnable = () => {
    const newName = `Runnable${runnables.length + 1}`
    setRunnables([
      ...runnables,
      {
        name: newName,
        criticality: 0,
        affinity: 0,
        period: 100,
        execution_time: 5,
        type: 'periodic',
        dependencies: [],
      },
    ])
  }

  const handleRemoveRunnable = (name: string) => {
    setRunnables((prev) =>
      prev
        .filter((runnable) => runnable.name !== name)
        .map((runnable) => ({
          ...runnable,
          dependencies: runnable.dependencies.filter(
            (dependency) => dependency !== name
          ),
        }))
    )
  }

  const handleRunnableChange = (
    name: string,
    field: keyof Runnable,
    value: number | string | string[] | 'periodic' | 'event'
  ) => {
    setRunnables((prev) =>
      prev.map((runnable) =>
        runnable.name === name ? { ...runnable, [field]: value } : runnable
      )
    )
  }

  const handleNameChange = (oldName: string, newName: string) => {
    if (!newName || oldName === newName) return
    setRunnables((prev) =>
      prev.map((runnable) => ({
        ...runnable,
        name: runnable.name === oldName ? newName : runnable.name,
        dependencies: runnable.dependencies.map((dependency) =>
          dependency === oldName ? newName : dependency
        ),
      }))
    )
  }

  const criticalityOptions = [
    { value: '0', label: '0 - ASIL A' },
    { value: '1', label: '1 - ASIL B' },
    { value: '2', label: '2 - ASIL C' },
    { value: '3', label: '3 - ASIL D' },
  ]

  const affinityOptions = Array.from({ length: numCores }, (_, i) => ({
    value: i.toString(),
    label: `Core ${i}`,
  }))

  const typeOptions = [
    { value: 'periodic', label: 'Periodic' },
    { value: 'event', label: 'Event' },
  ]

  return (
    <div className="w-full md:w-[400px]">
      <ScrollArea scrollbars="vertical">
        <Heading className="text-2xl font-bold mb-6 text-center">
          Configuration
        </Heading>
        <Flex direction="column" gap="2" mb="5">
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
        </Flex>
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
            {runnables
              .slice()
              .reverse()
              .map((runnable) => (
                <Box
                  key={runnable.name}
                  className="border rounded-lg p-4 bg-gray-50 relative"
                >
                  <div className="absolute top-2 right-2 z-20">
                    <IconButton
                      variant="ghost"
                      color="red"
                      onClick={() => handleRemoveRunnable(runnable.name)}
                      aria-label="Remove Runnable"
                    >
                      <Cross2Icon className="hover:cursor-pointer" />
                    </IconButton>
                  </div>
                  <Flex gap="2" align="center" mb="2">
                    <EditableRunnableName
                      name={runnable.name}
                      onRename={(newName) =>
                        handleNameChange(runnable.name, newName)
                      }
                    />
                  </Flex>
                  <Flex gap="3" wrap="wrap">
                    <ConfigSelectField
                      value={runnable.criticality}
                      field="criticality"
                      runnableName={runnable.name}
                      handleRunnableChange={handleRunnableChange}
                      options={criticalityOptions}
                      name="Criticality"
                    />
                    <ConfigSelectField
                      value={runnable.affinity}
                      field="affinity"
                      runnableName={runnable.name}
                      handleRunnableChange={handleRunnableChange}
                      options={affinityOptions}
                      name="Affinity"
                    />
                    <Flex direction="column" gap="1">
                      <Text size="2">Execution Time (ms)</Text>
                      <TextField.Root
                        type="number"
                        min={1}
                        value={runnable.execution_time}
                        onChange={(e) =>
                          handleRunnableChange(
                            runnable.name,
                            'execution_time',
                            Number(e.target.value) || 1
                          )
                        }
                        className="w-24"
                      />
                    </Flex>
                    <ConfigSelectField
                      value={runnable.type}
                      field="type"
                      runnableName={runnable.name}
                      handleRunnableChange={handleRunnableChange}
                      options={typeOptions}
                      name="Type"
                    />
                    {runnable.type === 'periodic' && (
                      <Flex direction="column" gap="1">
                        <Text size="2">Period (ms)</Text>
                        <TextField.Root
                          type="number"
                          min={1}
                          value={runnable.period || 100}
                          onChange={(e) =>
                            handleRunnableChange(
                              runnable.name,
                              'period',
                              Number(e.target.value) || 100
                            )
                          }
                          className="w-24"
                        />
                      </Flex>
                    )}
                    <Flex direction="column" gap="1">
                      <Text size="2">Dependencies</Text>
                      <DependencySelector
                        allRunnables={runnables
                          .filter((r) => r.name !== runnable.name)
                          .map((r) => r.name)}
                        selected={runnable.dependencies}
                        onChange={(deps) =>
                          handleRunnableChange(
                            runnable.name,
                            'dependencies',
                            deps
                          )
                        }
                      />
                    </Flex>
                  </Flex>
                </Box>
              ))}
          </Flex>
        </Box>
      </ScrollArea>
    </div>
  )
}

export default RunnableConfigPanel

interface EditableRunnableNameProps {
  name: string
  onRename: (newName: string) => void
}

const EditableRunnableName = ({
  name,
  onRename,
}: EditableRunnableNameProps) => {
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

interface ConfigSelectFieldProps {
  value: number | 'periodic' | 'event'
  field: keyof Runnable
  runnableName: string
  handleRunnableChange: (
    name: string,
    field: keyof Runnable,
    value: number
  ) => void
  options: { value: string; label: string }[]
  name: string
}

const ConfigSelectField = ({
  value,
  field,
  runnableName,
  handleRunnableChange,
  options,
  name,
}: ConfigSelectFieldProps) => {
  return (
    <Flex direction="column" gap="1">
      <Text size="2">{name}</Text>
      <Select.Root
        value={value.toString()}
        onValueChange={(value) =>
          handleRunnableChange(runnableName, field, Number(value))
        }
      >
        <Select.Trigger className="w-24" />
        <Select.Content>
          {options.map((option) => (
            <Select.Item key={option.value} value={option.value}>
              {option.label}
            </Select.Item>
          ))}
        </Select.Content>
      </Select.Root>
    </Flex>
  )
}
