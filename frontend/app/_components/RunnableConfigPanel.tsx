import { Runnable, SimulationForm } from '@/types/runnable'
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
import { useState } from 'react'
import { Controller, useFormContext } from 'react-hook-form'

const RunnableConfigPanel = () => {
  const { watch, register, setValue, control, handleSubmit, getValues } =
    useFormContext<SimulationForm>()

  const numCores = watch('numCores')
  const runnables = watch('runnables')
  const [resultId, setResultId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const onSubmit = async () => {
    setLoading(true)
    try {
      const values = getValues()
      const res = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })
      const data = await res.json()
      setResultId(data.resultId)
    } catch {
      alert('Simulation failed!')
    } finally {
      setLoading(false)
    }
  }

  const handleAddRunnable = () => {
    const newId = (
      Math.max(...runnables.map((runnable) => parseInt(runnable.id)), 0) + 1
    ).toString()
    const newName = `Runnable${newId}`
    setValue('runnables', [
      ...runnables,
      {
        id: newId,
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

  const handleRemoveRunnable = (id: string) => {
    setValue(
      'runnables',
      runnables
        .filter((runnable) => runnable.id !== id)
        .map((runnable) => ({
          ...runnable,
          dependencies: runnable.dependencies.filter(
            (dependencyId) => dependencyId !== id
          ),
        }))
    )
  }

  const criticalityOptions = [
    { value: '0', label: '0 - QM' },
    { value: '1', label: '1 - ASIL A' },
    { value: '2', label: '2 - ASIL B' },
    { value: '3', label: '3 - ASIL C' },
    { value: '4', label: '4 - ASIL D' },
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
        <form onSubmit={handleSubmit(onSubmit)}>
          <Heading className="text-2xl font-bold mb-6 text-center">
            Configuration
          </Heading>
          <Flex direction="column" gap="2" mb="5">
            <Text as="label" size="3" className="block mb-2 font-medium">
              Number of Cores
            </Text>
            <TextField.Root
              type="number"
              placeholder="1"
              {...register('numCores')}
              className="w-32"
            />
          </Flex>
          <Box mb="5">
            <Flex justify="between" align="center" mb="2">
              <Text as="label" size="3" className="font-medium">
                Runnables
              </Text>
              <Button variant="soft" onClick={handleAddRunnable} type="button">
                Add Runnable
              </Button>
            </Flex>
            <Flex direction="column" gap="4">
              {[...runnables].reverse().map((runnable) => {
                const originalIdx = runnables.findIndex(
                  (r) => r.id === runnable.id
                )
                return (
                  <Box
                    key={runnable.id}
                    className="border rounded-lg p-4 bg-gray-50 relative"
                  >
                    <div className="absolute top-2 right-2 z-20">
                      <IconButton
                        variant="ghost"
                        color="red"
                        onClick={() => handleRemoveRunnable(runnable.id)}
                        aria-label="Remove Runnable"
                      >
                        <Cross2Icon className="hover:cursor-pointer" />
                      </IconButton>
                    </div>
                    <Flex direction="column" gap="1">
                      <Text size="2">Runnable Name</Text>
                      <TextField.Root
                        className="w-24"
                        placeholder={`Runnable ${originalIdx + 1}`}
                        {...register(`runnables.${originalIdx}.name` as const)}
                      />
                    </Flex>
                    <Flex gap="3" wrap="wrap">
                      <ConfigSelectField
                        field="criticality"
                        options={criticalityOptions}
                        name="Criticality"
                        index={originalIdx}
                      />
                      <ConfigSelectField
                        field="affinity"
                        options={affinityOptions}
                        name="Affinity"
                        index={originalIdx}
                      />
                      <Flex direction="column" gap="1">
                        <Text size="2">Execution Time (ms)</Text>
                        <TextField.Root
                          type="number"
                          className="w-24"
                          {...register(
                            `runnables.${originalIdx}.execution_time` as const
                          )}
                        />
                      </Flex>
                      <ConfigSelectField
                        field="type"
                        options={typeOptions}
                        name="Type"
                        index={originalIdx}
                      />
                      {runnable.type === 'periodic' && (
                        <Flex direction="column" gap="1">
                          <Text size="2">Period (ms)</Text>
                          <TextField.Root
                            type="number"
                            className="w-24"
                            {...register(
                              `runnables.${originalIdx}.period` as const
                            )}
                          />
                        </Flex>
                      )}
                      <Flex direction="column" gap="1">
                        <Text size="2">Dependencies</Text>
                        <Controller
                          name={
                            `runnables.${originalIdx}.dependencies` as const
                          }
                          control={control}
                          render={({ field }) => (
                            <DependencySelector
                              allRunnables={runnables.map((r) => ({
                                id: r.id,
                                name: r.name,
                              }))}
                              selfId={runnable.id}
                              selected={field.value}
                              onChange={field.onChange}
                            />
                          )}
                        />
                      </Flex>
                    </Flex>
                  </Box>
                )
              })}
            </Flex>
          </Box>
          <div className="flex flex-col gap-2 mt-4">
            <Button type="submit" disabled={loading} variant="solid">
              {loading ? 'Running...' : 'Run Simulation'}
            </Button>
            {resultId && (
              <Button
                type="button"
                variant="outline"
                onClick={() => window.open(`/result/${resultId}`, '_blank')}
              >
                View Result
              </Button>
            )}
          </div>
        </form>
      </ScrollArea>
    </div>
  )
}

export default RunnableConfigPanel

interface DependencySelectorProps {
  allRunnables: { id: string; name: string }[]
  selfId: string
  selected: string[]
  onChange: (deps: string[]) => void
}

const DependencySelector = ({
  allRunnables,
  selfId,
  selected,
  onChange,
}: DependencySelectorProps) => {
  const [search, setSearch] = useState('')
  const [focused, setFocused] = useState(false)
  const filtered = allRunnables.filter(
    (runnable) =>
      runnable.name.toLowerCase().includes(search.toLowerCase()) &&
      !selected.includes(runnable.id) &&
      runnable.id !== selfId
  )

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-1 mb-1">
        {selected.map((depId) => {
          const dep = allRunnables.find((runnable) => runnable.id === depId)
          return (
            <span
              key={depId}
              className="inline-flex items-center bg-indigo-100 text-indigo-800 rounded px-2 py-0.5 text-xs mr-1"
            >
              {dep?.name || depId}
              <button
                type="button"
                className="ml-1 text-indigo-500 hover:text-red-500"
                onClick={() => onChange(selected.filter((d) => d !== depId))}
                aria-label={`Remove ${dep?.name || depId}`}
              >
                ×
              </button>
            </span>
          )
        })}
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
            onChange([...selected, filtered[0].id])
            setSearch('')
            e.preventDefault()
          }
        }}
      />
      {focused && filtered.length > 0 && (
        <div className="absolute left-0 right-0 border rounded bg-white shadow mt-1 max-h-32 overflow-y-auto z-10">
          {filtered.map((runnable) => (
            <div
              key={runnable.id}
              className="px-2 py-1 cursor-pointer hover:bg-indigo-100"
              onMouseDown={() => {
                onChange([...selected, runnable.id])
                setSearch('')
              }}
            >
              {runnable.name}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface ConfigSelectFieldProps {
  field: keyof Runnable
  options: { value: string; label: string }[]
  name: string
  index: number
}

const ConfigSelectField = ({
  field,
  options,
  name,
  index,
}: ConfigSelectFieldProps) => {
  const { control } = useFormContext<SimulationForm>()

  return (
    <Flex direction="column" gap="1">
      <Text size="2">{name}</Text>
      <Controller
        control={control}
        name={`runnables.${index}.${field}` as const}
        render={({ field: controllerField }) => (
          <Select.Root
            value={controllerField.value?.toString() ?? ''}
            onValueChange={(val) => {
              if (field === 'type') {
                controllerField.onChange(val)
              } else {
                controllerField.onChange(Number(val))
              }
            }}
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
        )}
      />
    </Flex>
  )
}
