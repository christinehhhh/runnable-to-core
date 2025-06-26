import { useState } from 'react'

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

export default DependencySelector
