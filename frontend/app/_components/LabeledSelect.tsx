import { Flex, Text, Select } from '@radix-ui/themes'
import { ReactNode } from 'react'

interface LabeledSelectProps {
  label: string
  value: string
  onValueChange: (value: string) => void
  children: ReactNode
  className?: string
}

const LabeledSelect = ({
  label,
  value,
  onValueChange,
  children,
  className,
}: LabeledSelectProps) => (
  <Flex direction="column" gap="1">
    <Text size="2">{label}</Text>
    <Select.Root value={value} onValueChange={onValueChange}>
      <Select.Trigger className={className || ''} />
      <Select.Content>{children}</Select.Content>
    </Select.Root>
  </Flex>
)

export default LabeledSelect
