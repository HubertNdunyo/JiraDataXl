'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { 
  ArrowRight, 
  ArrowLeft, 
  Wand2, 
  Search, 
  FileJson, 
  CheckCircle2,
  AlertCircle,
  Sparkles,
  X
} from 'lucide-react'
import { FieldSearchInput } from './field-search-input'
import { FieldPreview } from './field-preview'
import { toast } from '@/hooks/use-toast'

interface MappingWizardProps {
  open: boolean
  onClose: () => void
  onComplete: (mappings: any) => void
  cachedFields?: any
  existingConfig?: any
}

type WizardStep = 'welcome' | 'mode' | 'selection' | 'mapping' | 'review'

interface FieldMapping {
  fieldKey: string
  fieldName: string
  type: string
  required: boolean
  instance1?: { field_id: string; name: string }
  instance2?: { field_id: string; name: string }
}

// Common field keywords to prioritize in smart mode
const COMMON_FIELD_KEYWORDS = [
  'order', 'number', 'client', 'customer', 'name', 'email', 'address', 
  'service', 'type', 'photo', 'raw', 'edited', 'dropbox', 'link',
  'schedule', 'date', 'time', 'team', 'editor', 'notes', 'comment',
  'instruction', 'special', 'access', 'status', 'priority'
]

export function MappingWizard({ open, onClose, onComplete, cachedFields, existingConfig }: MappingWizardProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>('welcome')
  const [mode, setMode] = useState<'smart' | 'manual'>('smart')
  const [selectedFields, setSelectedFields] = useState<string[]>([])
  const [fieldMappings, setFieldMappings] = useState<Record<string, FieldMapping>>({})
  const [isProcessing, setIsProcessing] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  // Get all currently mapped field IDs
  const getMappedFieldIds = () => {
    const mappedIds = new Set<string>()
    if (existingConfig?.field_groups) {
      Object.values(existingConfig.field_groups).forEach((group: any) => {
        if (group.fields) {
          Object.values(group.fields).forEach((field: any) => {
            if (field.instance_1?.field_id) mappedIds.add(field.instance_1.field_id)
            if (field.instance_2?.field_id) mappedIds.add(field.instance_2.field_id)
          })
        }
      })
    }
    return mappedIds
  }

  // Get available unmapped fields from both instances
  const getAvailableFields = () => {
    const mappedIds = getMappedFieldIds()
    const fieldsByName = new Map<string, any>()
    
    if (cachedFields?.fields) {
      // Process fields from both instances and group by name
      ['instance_1', 'instance_2'].forEach(instance => {
        const instanceFields = cachedFields.fields[instance]
        if (instanceFields) {
          // Combine system and custom fields
          const allFields = [...(instanceFields.system || []), ...(instanceFields.custom || [])]
          
          allFields.forEach((field: any) => {
            // Skip if already mapped
            if (mappedIds.has(field.field_id)) return
            
            const fieldName = field.field_name
            
            if (fieldsByName.has(fieldName)) {
              // Field with same name exists, add this instance's info
              const existingField = fieldsByName.get(fieldName)
              
              // Add instance to the list
              if (!existingField.instances.includes(instance)) {
                existingField.instances.push(instance)
              }
              
              // Store field IDs for each instance
              if (!existingField.field_ids) {
                existingField.field_ids = {}
              }
              existingField.field_ids[instance] = field.field_id
              
              // Use the first field's type and other properties
              // They should be the same across instances for the same field
            } else {
              // New field, create entry
              fieldsByName.set(fieldName, {
                field_name: field.field_name,
                field_type: field.field_type,
                is_custom: field.is_custom,
                is_array: field.is_array,
                instances: [instance],
                field_ids: { [instance]: field.field_id },
                uniqueId: `field_${fieldName.replace(/[^a-zA-Z0-9]/g, '_')}`,
                score: calculateFieldScore(field.field_name),
                isMapped: false
              })
            }
          })
        }
      })
    }
    
    // Convert map to array and sort
    const availableFields = Array.from(fieldsByName.values())
    return availableFields.sort((a, b) => {
      // First sort by score (relevance)
      if (b.score !== a.score) return b.score - a.score
      // Then by field name
      return a.field_name.localeCompare(b.field_name)
    })
  }

  // Calculate relevance score based on common field keywords
  const calculateFieldScore = (fieldName: string) => {
    const nameLower = fieldName.toLowerCase()
    let score = 0
    
    COMMON_FIELD_KEYWORDS.forEach(keyword => {
      if (nameLower.includes(keyword)) {
        score += 10
      }
    })
    
    // Boost score for custom fields (they're usually more relevant)
    if (fieldName.startsWith('customfield_')) {
      score += 5
    }
    
    return score
  }

  // Reset wizard state when opened
  useEffect(() => {
    if (open) {
      setCurrentStep('welcome')
      setMode('smart')
      setSelectedFields([])
      setFieldMappings({})
      setSearchTerm('')
    }
  }, [open])

  const getProgress = () => {
    const steps: WizardStep[] = ['welcome', 'mode', 'selection', 'mapping', 'review']
    const currentIndex = steps.indexOf(currentStep)
    return ((currentIndex + 1) / steps.length) * 100
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
      object: 'bg-gray-100 text-gray-800',
      user: 'bg-indigo-100 text-indigo-800',
      option: 'bg-yellow-100 text-yellow-800'
    }
    return typeColors[type] || 'bg-gray-100 text-gray-800'
  }

  const handleNext = () => {
    const stepOrder: WizardStep[] = ['welcome', 'mode', 'selection', 'mapping', 'review']
    const currentIndex = stepOrder.indexOf(currentStep)
    if (currentIndex < stepOrder.length - 1) {
      setCurrentStep(stepOrder[currentIndex + 1])
    }
  }

  const handleBack = () => {
    const stepOrder: WizardStep[] = ['welcome', 'mode', 'selection', 'mapping', 'review']
    const currentIndex = stepOrder.indexOf(currentStep)
    if (currentIndex > 0) {
      setCurrentStep(stepOrder[currentIndex - 1])
    }
  }

  const toggleFieldSelection = (fieldKey: string) => {
    setSelectedFields(prev => 
      prev.includes(fieldKey) 
        ? prev.filter(k => k !== fieldKey)
        : [...prev, fieldKey]
    )
  }

  const initializeFieldMappings = () => {
    const availableFields = getAvailableFields()
    const mappings: Record<string, FieldMapping> = {}
    
    selectedFields.forEach((uniqueId) => {
      const field = availableFields.find(f => f.uniqueId === uniqueId)
      if (field) {
        // Generate a unique key for each mapping
        const baseKey = field.field_name
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '_')
          .replace(/^_|_$/g, '')
        
        // Ensure unique keys if multiple fields have similar names
        let fieldKey = baseKey
        let counter = 1
        while (mappings[fieldKey]) {
          fieldKey = `${baseKey}_${counter}`
          counter++
        }
        
        mappings[fieldKey] = {
          fieldKey,
          fieldName: field.field_name,
          type: field.field_type || 'string',
          required: false,
        }
        
        // Pre-populate instances where this field exists
        if (field.field_ids.instance_1) {
          mappings[fieldKey].instance1 = {
            field_id: field.field_ids.instance_1,
            name: field.field_name
          }
        }
        if (field.field_ids.instance_2) {
          mappings[fieldKey].instance2 = {
            field_id: field.field_ids.instance_2,
            name: field.field_name
          }
        }
      }
    })
    
    setFieldMappings(mappings)
    
    if (mode === 'smart') {
      // In smart mode, try to find matching fields in the other instance
      // for fields that only exist in one instance
      performSmartMapping(mappings)
    }
  }

  const performSmartMapping = async (mappings: Record<string, FieldMapping>) => {
    setIsProcessing(true)
    
    // Smart mapping tries to find best matching fields in missing instances
    const updatedMappings = { ...mappings }
    
    for (const [fieldKey, mapping] of Object.entries(updatedMappings)) {
      if (cachedFields?.fields) {
        const searchTerms = mapping.fieldName.toLowerCase().split(/[^a-z0-9]+/).filter(t => t.length > 2)
        
        // Only search for instance 1 if it's missing
        if (!mapping.instance1) {
          const instance1Fields = [...(cachedFields.fields.instance_1?.system || []), ...(cachedFields.fields.instance_1?.custom || [])]
          const instance1Matches = instance1Fields
            .map((field: any) => {
              const fieldNameLower = field.field_name.toLowerCase()
              let score = 0
              
              // Exact match gets highest score
              if (fieldNameLower === mapping.fieldName.toLowerCase()) {
                score = 100
              } else {
                // Score based on matching terms
                searchTerms.forEach(term => {
                  if (fieldNameLower.includes(term)) score += 10
                })
              }
              
              return { field, score }
            })
            .filter(item => item.score > 0)
            .sort((a, b) => b.score - a.score)
          
          if (instance1Matches.length > 0) {
            const bestMatch = instance1Matches[0].field
            updatedMappings[fieldKey].instance1 = {
              field_id: bestMatch.field_id,
              name: bestMatch.field_name
            }
          }
        }
        
        // Only search for instance 2 if it's missing
        if (!mapping.instance2) {
          const instance2Fields = [...(cachedFields.fields.instance_2?.system || []), ...(cachedFields.fields.instance_2?.custom || [])]
          const instance2Matches = instance2Fields
            .map((field: any) => {
              const fieldNameLower = field.field_name.toLowerCase()
              let score = 0
              
              // Exact match gets highest score
              if (fieldNameLower === mapping.fieldName.toLowerCase()) {
                score = 100
              } else {
                // Score based on matching terms
                searchTerms.forEach(term => {
                  if (fieldNameLower.includes(term)) score += 10
                })
              }
              
              return { field, score }
            })
            .filter(item => item.score > 0)
            .sort((a, b) => b.score - a.score)
          
          if (instance2Matches.length > 0) {
            const bestMatch = instance2Matches[0].field
            updatedMappings[fieldKey].instance2 = {
              field_id: bestMatch.field_id,
              name: bestMatch.field_name
            }
          }
        }
      }
    }
    
    setFieldMappings(updatedMappings)
    setIsProcessing(false)
  }

  const handleComplete = () => {
    // Get the existing config structure or create a new one
    const baseConfig = existingConfig || {
      version: "2.0",
      last_updated: new Date().toISOString(),
      description: "JIRA field mappings configuration",
      instances: {
        instance_1: {
          url: "https://betteredits.atlassian.net",
          name: "BetterEdits Instance 1"
        },
        instance_2: {
          url: "https://betteredits2.atlassian.net", 
          name: "BetterEdits Instance 2"
        }
      },
      field_groups: {}
    }
    
    // Get existing Wizard Fields group or create new one
    const existingWizardGroup = baseConfig.field_groups["Wizard Fields"] || {
      description: "Fields added via configuration wizard",
      fields: {}
    }
    
    // Merge new mappings with existing ones
    const mergedFields = { ...existingWizardGroup.fields }
    
    // Convert wizard mappings to proper format and add to merged fields
    Object.entries(fieldMappings).forEach(([key, mapping]) => {
      // Check if this field already exists (by field name or key)
      const existingKey = Object.keys(mergedFields).find(k => 
        mergedFields[k].description === mapping.fieldName || k === key
      )
      
      if (existingKey) {
        // Update existing field mapping
        const instance1Mapping = mapping.instance1 ? {
          field_id: mapping.instance1.field_id,
          name: mapping.instance1.name,
          description: null
        } : mergedFields[existingKey].instance_1
        
        const instance2Mapping = mapping.instance2 ? {
          field_id: mapping.instance2.field_id,
          name: mapping.instance2.name,
          description: null
        } : mergedFields[existingKey].instance_2
        
        mergedFields[existingKey] = {
          ...mergedFields[existingKey],
          type: mapping.type,
          required: mapping.required,
          description: mapping.fieldName,
          instance_1: instance1Mapping,
          instance_2: instance2Mapping
        }
      } else {
        // Add new field mapping
        const instance1Mapping = mapping.instance1 ? {
          field_id: mapping.instance1.field_id,
          name: mapping.instance1.name,
          description: null
        } : null
        
        const instance2Mapping = mapping.instance2 ? {
          field_id: mapping.instance2.field_id,
          name: mapping.instance2.name,
          description: null
        } : null

        mergedFields[key] = {
          type: mapping.type,
          required: mapping.required,
          description: mapping.fieldName,
          system_field: false,
          field_id: null,
          instance_1: instance1Mapping,
          instance_2: instance2Mapping
        }
      }
    })

    // Create the updated configuration
    const updatedConfig = {
      ...baseConfig,
      last_updated: new Date().toISOString(),
      field_groups: {
        ...baseConfig.field_groups,
        "Wizard Fields": {
          description: "Fields added via configuration wizard",
          fields: mergedFields
        }
      }
    }
    
    // Count how many fields were added/updated
    const newFieldCount = Object.keys(fieldMappings).length
    const totalFieldCount = Object.keys(mergedFields).length
    
    if (newFieldCount > 0) {
      onComplete(updatedConfig)
      
      toast({
        title: "Wizard Complete",
        description: `Successfully added/updated ${newFieldCount} field mappings. Total: ${totalFieldCount} fields`
      })
    } else {
      toast({
        title: "No Fields Configured",
        description: "Please configure at least one field mapping",
        variant: "destructive"
      })
    }
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 'welcome':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <Wand2 className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Welcome to the Field Mapping Wizard</h3>
              <p className="text-gray-600">
                This wizard will help you set up field mappings between your JIRA instances
                and the sync system. We'll guide you through each step.
              </p>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium">Choose your mapping mode</p>
                  <p className="text-sm text-gray-600">Smart mode uses AI to suggest mappings</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium">Select fields to map</p>
                  <p className="text-sm text-gray-600">Choose from commonly used fields</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium">Review and confirm</p>
                  <p className="text-sm text-gray-600">Preview your mappings before saving</p>
                </div>
              </div>
            </div>
          </div>
        )

      case 'mode':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Choose Mapping Mode</h3>
              <p className="text-gray-600">
                Select how you want to map your fields
              </p>
            </div>

            <RadioGroup value={mode} onValueChange={(value: 'smart' | 'manual') => setMode(value)}>
              <div className="space-y-4">
                <Card className={mode === 'smart' ? 'border-blue-500' : ''}>
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <RadioGroupItem value="smart" id="smart" className="mt-1" />
                      <div className="flex-1">
                        <Label htmlFor="smart" className="flex items-center gap-2 cursor-pointer">
                          <Sparkles className="w-4 h-4 text-blue-600" />
                          <span className="font-medium">Smart Mapping</span>
                          <Badge variant="secondary" className="text-xs">Recommended</Badge>
                        </Label>
                        <p className="text-sm text-gray-600 mt-1">
                          Automatically suggests field mappings based on field names and types.
                          You can review and adjust the suggestions.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className={mode === 'manual' ? 'border-blue-500' : ''}>
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <RadioGroupItem value="manual" id="manual" className="mt-1" />
                      <div className="flex-1">
                        <Label htmlFor="manual" className="flex items-center gap-2 cursor-pointer">
                          <FileJson className="w-4 h-4 text-gray-600" />
                          <span className="font-medium">Manual Mapping</span>
                        </Label>
                        <p className="text-sm text-gray-600 mt-1">
                          Manually select each field mapping. Best for custom or complex field structures.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </RadioGroup>
          </div>
        )

      case 'selection':
        const availableFields = getAvailableFields()
        
        // Filter fields based on search term
        const filteredFields = searchTerm 
          ? availableFields.filter(field => {
              const search = searchTerm.toLowerCase()
              return field.field_name.toLowerCase().includes(search) || 
                     field.field_id.toLowerCase().includes(search)
            })
          : availableFields
        
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Select Fields to Map</h3>
              <p className="text-gray-600">
                Choose from discovered JIRA fields that haven't been mapped yet
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Showing {filteredFields.length} of {availableFields.length} unmapped fields
                {selectedFields.length > 0 && (
                  <span className="ml-2 text-blue-600">
                    • {selectedFields.length} selected
                  </span>
                )}
              </p>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                placeholder="Search by field name or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    setSearchTerm('')
                  }
                }}
                className="pl-10"
                autoFocus
              />
              {searchTerm && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSearchTerm('')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>

            {availableFields.length === 0 ? (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  No unmapped fields found. All discovered fields are already configured.
                  You may need to run field discovery first.
                </AlertDescription>
              </Alert>
            ) : filteredFields.length === 0 ? (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  No fields match your search "{searchTerm}". Try different keywords.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                {filteredFields.map((field) => {
                  const isMapped = field.isMapped
                  const isSelected = selectedFields.includes(field.uniqueId)
                  return (
                    <Card 
                      key={field.uniqueId} 
                      className={`${isSelected ? 'border-blue-500' : ''} ${isMapped ? 'opacity-50' : ''}`}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center gap-3">
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={() => !isMapped && toggleFieldSelection(field.uniqueId)}
                            id={field.uniqueId}
                            disabled={isMapped}
                          />
                          <div className="flex-1">
                            <Label htmlFor={field.uniqueId} className={`${isMapped ? '' : 'cursor-pointer'}`}>
                              <div className={`font-medium ${isMapped ? 'text-gray-400' : ''}`}>
                                {field.field_name}
                                {isMapped && <span className="ml-2 text-xs text-gray-400">(Already Mapped)</span>}
                              </div>
                              <div className="text-xs text-gray-500">
                                {field.instances.map((inst: string) => (
                                  <div key={inst}>
                                    {inst.replace(/_/g, ' ')}: {field.field_ids[inst]}
                                  </div>
                                ))}
                              </div>
                            </Label>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge 
                              variant="outline" 
                              className={getFieldTypeColor(field.field_type)}
                            >
                              {field.field_type}
                            </Badge>
                            {field.is_array && (
                              <Badge variant="secondary" className="text-xs">
                                Array
                              </Badge>
                            )}
                            {field.is_custom ? (
                              <Badge variant="outline" className="text-xs">
                                Custom
                              </Badge>
                            ) : (
                              <Badge variant="default" className="text-xs">
                                System
                              </Badge>
                            )}
                            {field.score > 0 && !isMapped && (
                              <span title={`Relevance score: ${field.score}`}>
                                <Sparkles className="w-4 h-4 text-amber-500" />
                              </span>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            )}

            {selectedFields.length === 0 && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Please select at least one field to continue
                </AlertDescription>
              </Alert>
            )}
          </div>
        )

      case 'mapping':
        // Initialize mappings when entering this step
        if (Object.keys(fieldMappings).length === 0 && selectedFields.length > 0) {
          initializeFieldMappings()
          return (
            <div className="text-center py-8">
              <Sparkles className="w-8 h-8 text-blue-600 mx-auto mb-2 animate-pulse" />
              <p className="text-gray-600">Preparing field mappings...</p>
            </div>
          )
        }

        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Configure Field Mappings</h3>
              <p className="text-gray-600">
                {mode === 'smart' ? 'Review and adjust the suggested mappings' : 'Map each field to JIRA fields'}
              </p>
            </div>

            {isProcessing && (
              <div className="text-center py-8">
                <Sparkles className="w-8 h-8 text-blue-600 mx-auto mb-2 animate-pulse" />
                <p className="text-gray-600">Finding best matches...</p>
              </div>
            )}

            {!isProcessing && (
              <div className="space-y-4 max-h-[400px] overflow-y-auto">
                {Object.entries(fieldMappings).map(([key, mapping]) => (
                  <Card key={key}>
                    <CardContent className="p-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium">{mapping.fieldName}</h4>
                            <p className="text-xs text-gray-500">
                              {key} • {mapping.type}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{mapping.type}</Badge>
                            {mapping.required && (
                              <Badge variant="destructive" className="text-xs">Required</Badge>
                            )}
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <Label className="text-sm">Instance 1</Label>
                              {mapping.instance1?.field_id && (
                                <FieldPreview
                                  fieldId={mapping.instance1.field_id}
                                  instance="instance_1"
                                  fieldName={mapping.instance1.name}
                                />
                              )}
                            </div>
                            <FieldSearchInput
                              value={mapping.instance1?.field_id || ''}
                              onChange={(fieldId) => {
                                const fields = cachedFields?.fields?.instance_1 || { system: [], custom: [] }
                                const allFields = [...fields.system, ...fields.custom]
                                const selectedField = allFields.find((f: any) => f.field_id === fieldId)
                                
                                setFieldMappings(prev => ({
                                  ...prev,
                                  [key]: {
                                    ...prev[key],
                                    instance1: {
                                      field_id: fieldId,
                                      name: selectedField?.field_name || ''
                                    }
                                  }
                                }))
                              }}
                              instance="instance_1"
                              cachedFields={cachedFields}
                              existingMappings={Array.from(getMappedFieldIds())}
                            />
                          </div>

                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <Label className="text-sm">Instance 2</Label>
                              {mapping.instance2?.field_id && (
                                <FieldPreview
                                  fieldId={mapping.instance2.field_id}
                                  instance="instance_2"
                                  fieldName={mapping.instance2.name}
                                />
                              )}
                            </div>
                            <FieldSearchInput
                              value={mapping.instance2?.field_id || ''}
                              onChange={(fieldId) => {
                                const fields = cachedFields?.fields?.instance_2 || { system: [], custom: [] }
                                const allFields = [...fields.system, ...fields.custom]
                                const selectedField = allFields.find((f: any) => f.field_id === fieldId)
                                
                                setFieldMappings(prev => ({
                                  ...prev,
                                  [key]: {
                                    ...prev[key],
                                    instance2: {
                                      field_id: fieldId,
                                      name: selectedField?.field_name || ''
                                    }
                                  }
                                }))
                              }}
                              instance="instance_2"
                              cachedFields={cachedFields}
                              existingMappings={Array.from(getMappedFieldIds())}
                            />
                          </div>
                        </div>

                        {mode === 'smart' && mapping.instance1?.field_id && mapping.instance2?.field_id && (
                          <div className="flex items-center gap-2 text-sm text-green-600">
                            <Sparkles className="w-4 h-4" />
                            <span>Smart match found</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )

      case 'review':
        const mappedCount = Object.values(fieldMappings).filter(
          m => m.instance1?.field_id || m.instance2?.field_id
        ).length
        const totalCount = Object.keys(fieldMappings).length

        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Review Your Configuration</h3>
              <p className="text-gray-600">
                Please review your field mappings before completing the wizard
              </p>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Mapping Progress</span>
                <span className="text-sm text-gray-600">{mappedCount} of {totalCount} fields mapped</span>
              </div>
              <Progress value={(mappedCount / totalCount) * 100} className="h-2" />
            </div>

            <div className="space-y-2 max-h-[350px] overflow-y-auto">
              {Object.entries(fieldMappings).map(([key, mapping]) => {
                const isMapped = mapping.instance1?.field_id || mapping.instance2?.field_id
                
                return (
                  <Card key={key} className={!isMapped ? 'border-amber-200' : ''}>
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{mapping.fieldName}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {mapping.instance1?.field_id && (
                              <div>Instance 1: {mapping.instance1.name}</div>
                            )}
                            {mapping.instance2?.field_id && (
                              <div>Instance 2: {mapping.instance2.name}</div>
                            )}
                            {!isMapped && (
                              <div className="text-amber-600">Not mapped</div>
                            )}
                          </div>
                        </div>
                        <div>
                          {isMapped ? (
                            <CheckCircle2 className="w-5 h-5 text-green-600" />
                          ) : (
                            <AlertCircle className="w-5 h-5 text-amber-600" />
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>

            {mappedCount < totalCount && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Some fields are not fully mapped. You can complete the wizard and configure them later.
                </AlertDescription>
              </Alert>
            )}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Field Mapping Wizard</span>
          </DialogTitle>
          <DialogDescription>
            {currentStep === 'welcome' && 'Configure field mappings between JIRA instances'}
            {currentStep === 'mode' && 'Choose how you want to configure field mappings'}
            {currentStep === 'selection' && 'Select fields to map'}
            {currentStep === 'mapping' && 'Map fields between instances'}
            {currentStep === 'review' && 'Review and save your field mappings'}
          </DialogDescription>
          <div className="absolute top-4 right-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>
        <div className="mt-4">
          <Progress value={getProgress()} className="h-2" />
        </div>

        <div className="min-h-[400px] py-6">
          {renderStepContent()}
        </div>

        <DialogFooter className="flex justify-between">
          <div>
            {currentStep !== 'welcome' && (
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
            )}
          </div>
          
          <div className="flex gap-2">
            {currentStep === 'review' ? (
              <Button onClick={handleComplete}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Complete Setup
              </Button>
            ) : (
              <Button 
                onClick={handleNext}
                disabled={
                  (currentStep === 'selection' && selectedFields.length === 0) ||
                  isProcessing
                }
              >
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}