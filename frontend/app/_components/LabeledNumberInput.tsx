import { Flex, Text, TextField } from '@radix-ui/themes'

interface LabeledNumberInputProps {
  label: string
  value: number
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  min: number
  max?: number
  className?: string
}

const LabeledNumberInput = ({
  label,
  value,
  onChange,
  min,
  max,
  className,
}: LabeledNumberInputProps) => (
  <Flex direction="column" gap="1">
    <Text size="2">{label}</Text>
    <TextField.Root
      type="number"
      min={min}
      max={max}
      value={value}
      onChange={onChange}
      className={className || ''}
    />
  </Flex>
)

export default LabeledNumberInput
