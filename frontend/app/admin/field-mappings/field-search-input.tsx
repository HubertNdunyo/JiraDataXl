'use client'

import { useState, useEffect, useRef, useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, Check, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FieldSearchInputProps {
  value: string
  onChange: (value: string) => void
  instance: 'instance_1' | 'instance_2'
  placeholder?: string
  cachedFields?: any
  existingMappings?: string[]
}

export function FieldSearchInput({
  value,
  onChange,
  instance,
  placeholder = "Search for field...",
  cachedFields,
  existingMappings = []
}: FieldSearchInputProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [hasInitialized, setHasInitialized] = useState(false)
  const [filteredFields, setFilteredFields] = useState<any[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Get fields for the specific instance - memoize to prevent recreating on every render
  const instanceFields = cachedFields?.fields?.[instance] || { system: [], custom: [] }
  const allFields = useMemo(() => 
    [...instanceFields.system, ...instanceFields.custom],
    [instanceFields.system, instanceFields.custom]
  )

  // Initialize search term with current field name if value is set
  useEffect(() => {
    if (value && !hasInitialized && allFields.length > 0) {
      const currentField = allFields.find((f: any) => f.field_id === value)
      if (currentField) {
        setSearchTerm(currentField.field_name)
        setHasInitialized(true)
      }
    }
  }, [value, hasInitialized, allFields])

  useEffect(() => {
    if (!searchTerm) {
      setFilteredFields([])
      setSelectedIndex(0)
      return
    }

    const search = searchTerm.toLowerCase()
    const filtered = allFields.filter((field: any) => {
      // Skip already mapped fields (but allow current value)
      if (field.field_id !== value && existingMappings.includes(field.field_id)) {
        return false
      }
      const nameMatch = field.field_name.toLowerCase().includes(search)
      const idMatch = field.field_id.toLowerCase().includes(search)
      return nameMatch || idMatch
    }).slice(0, 10) // Limit to 10 results

    setFilteredFields(filtered)
    setSelectedIndex(0)
  }, [searchTerm, allFields, existingMappings, value])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || filteredFields.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => Math.min(prev + 1, filteredFields.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (filteredFields[selectedIndex]) {
          selectField(filteredFields[selectedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        break
    }
  }

  const selectField = (field: any) => {
    onChange(field.field_id)
    setSearchTerm(field.field_name)
    setIsOpen(false)
  }

  const isFieldMapped = (fieldId: string) => {
    return existingMappings.includes(fieldId)
  }

  const getFieldTypeColor = (type: string) => {
    const typeColors: Record<string, string> = {
      string: 'bg-blue-100 text-blue-800',
      number: 'bg-green-100 text-green-800',
      integer: 'bg-green-100 text-green-800',
      boolean: 'bg-purple-100 text-purple-800',
      date: 'bg-orange-100 text-orange-800',
      datetime: 'bg-orange-100 text-orange-800',
      array: 'bg-pink-100 text-pink-800',
      object: 'bg-gray-100 text-gray-800'
    }
    return typeColors[type] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
        <Input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value)
            setIsOpen(true)
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="pl-10"
        />
        {value && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <Badge variant="secondary" className="text-xs">
              {value}
            </Badge>
          </div>
        )}
      </div>

      {isOpen && filteredFields.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-64 overflow-auto">
          {filteredFields.map((field, index) => {
            const isMapped = isFieldMapped(field.field_id)
            return (
              <div
                key={field.field_id}
                onClick={() => !isMapped && selectField(field)}
                className={cn(
                  "px-3 py-2 cursor-pointer flex items-center justify-between",
                  index === selectedIndex && "bg-gray-100",
                  isMapped && "opacity-50 cursor-not-allowed"
                )}
              >
                <div className="flex-1">
                  <div className="font-medium text-sm">{field.field_name}</div>
                  <div className="text-xs text-gray-500">{field.field_id}</div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant="outline" 
                    className={cn("text-xs", getFieldTypeColor(field.field_type))}
                  >
                    {field.field_type}
                  </Badge>
                  {isMapped && (
                    <Badge variant="secondary" className="text-xs">
                      Mapped
                    </Badge>
                  )}
                  {field.field_id === value && (
                    <Check className="w-4 h-4 text-green-600" />
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {isOpen && searchTerm && filteredFields.length === 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg p-3">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <AlertCircle className="w-4 h-4" />
            No fields found matching "{searchTerm}"
          </div>
        </div>
      )}
    </div>
  )
}