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
} from '@radix-ui/themes'
import DependencySelector from './DependencySelector'
import EditableRunnableName from './EditableRunnableName'
import LabeledNumberInput from './LabeledNumberInput'
import LabeledSelect from './LabeledSelect'

import { Runnable, RunnableConfig } from '../types/runnableTypes'

interface Props {
  numCores: number
  setNumCores: (n: number) => void
  runnables: RunnableConfig
  setRunnables: React.Dispatch<React.SetStateAction<RunnableConfig>>
}

const RunnableConfigPanel = ({
  numCores,
  setNumCores,
  runnables,
  setRunnables,
}: Props) => {
  const handleAddRunnable = () => {
    const newName = `Runnable${Object.keys(runnables).length + 1}`
    setRunnables((prev) => ({
      ...prev,
      [newName]: {
        criticality: 0,
        affinity: 0,
        period: 100,
        execution_time: 5,
        type: 'periodic',
        deps: [],
      },
    }))
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
    <ScrollArea scrollbars="vertical">
      <Heading className="text-2xl font-bold mb-6 text-center">
        Configuration
      </Heading>
      <Flex direction="column" gap="2" mb="5">
        <Text as="label" size="3" className="block mb-2 font-medium">
          Number of Cores
        </Text>
        <LabeledNumberInput
          label="Number of Cores"
          value={numCores}
          onChange={(e) => setNumCores(Number(e.target.value) || 1)}
          min={1}
          max={16}
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
          {Object.entries(runnables)
            .reverse()
            .map(([name, runnable]) => (
              <Box
                key={name}
                className="border rounded-lg p-4 bg-gray-50 relative"
              >
                <div className="absolute top-2 right-2 z-20">
                  <IconButton
                    variant="ghost"
                    color="red"
                    onClick={() => handleRemoveRunnable(name)}
                    aria-label="Remove Runnable"
                  >
                    <Cross2Icon className="hover:cursor-pointer" />
                  </IconButton>
                </div>
                <Flex gap="2" align="center" mb="2">
                  <EditableRunnableName
                    name={name}
                    onRename={(newName) => handleNameChange(name, newName)}
                  />
                </Flex>
                <Flex gap="3" wrap="wrap">
                  <LabeledSelect
                    label="Criticality"
                    value={runnable.criticality.toString()}
                    onValueChange={(value) =>
                      handleRunnableChange(name, 'criticality', Number(value))
                    }
                    className="w-24"
                  >
                    <Select.Item value="0">0 - ASIL A</Select.Item>
                    <Select.Item value="1">1 - ASIL B</Select.Item>
                    <Select.Item value="2">2 - ASIL C</Select.Item>
                    <Select.Item value="3">3 - ASIL D</Select.Item>
                  </LabeledSelect>
                  <LabeledSelect
                    label="Affinity"
                    value={runnable.affinity.toString()}
                    onValueChange={(value) =>
                      handleRunnableChange(name, 'affinity', Number(value))
                    }
                    className="w-20"
                  >
                    {Array.from({ length: numCores }, (_, i) => (
                      <Select.Item key={i} value={i.toString()}>
                        Core {i}
                      </Select.Item>
                    ))}
                  </LabeledSelect>
                  <LabeledNumberInput
                    label="Execution Time (ms)"
                    value={runnable.execution_time}
                    onChange={(e) =>
                      handleRunnableChange(
                        name,
                        'execution_time',
                        Number(e.target.value) || 1
                      )
                    }
                    min={1}
                    className="w-24"
                  />
                  <LabeledSelect
                    label="Type"
                    value={runnable.type}
                    onValueChange={(value) =>
                      handleRunnableChange(
                        name,
                        'type',
                        value as 'periodic' | 'event'
                      )
                    }
                    className="w-28"
                  >
                    <Select.Item value="periodic">Periodic</Select.Item>
                    <Select.Item value="event">Event</Select.Item>
                  </LabeledSelect>
                  {runnable.type === 'periodic' && (
                    <LabeledNumberInput
                      label="Period (ms)"
                      value={runnable.period || 100}
                      onChange={(e) =>
                        handleRunnableChange(
                          name,
                          'period',
                          Number(e.target.value) || 100
                        )
                      }
                      min={1}
                      className="w-24"
                    />
                  )}
                  <DependencySelector
                    allRunnables={Object.keys(runnables).filter(
                      (n) => n !== name
                    )}
                    selected={runnable.deps}
                    onChange={(deps) =>
                      handleRunnableChange(name, 'deps', deps)
                    }
                  />
                </Flex>
              </Box>
            ))}
        </Flex>
      </Box>
    </ScrollArea>
  )
}

export default RunnableConfigPanel
