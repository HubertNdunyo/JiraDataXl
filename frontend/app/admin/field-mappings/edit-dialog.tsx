'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Save, X } from 'lucide-react'
import { FieldSearchInput } from './field-search-input'
import { FieldPreview } from './field-preview'

interface FieldEditDialogProps {
  open: boolean
  onClose: () => void
  onSave: (field: any) => void
  field?: any
  fieldKey?: string
  groupKey?: string
  cachedFields?: any
  existingMappings?: string[]
}

export function FieldEditDialog({ 
  open, 
  onClose, 
  onSave, 
  field, 
  fieldKey,
  groupKey,
  cachedFields,
  existingMappings = []
}: FieldEditDialogProps) {
  const [editedField, setEditedField] = useState(field || {
    type: 'string',
    required: false,
    description: '',
    instance_1: { field_id: '', name: '' },
    instance_2: { field_id: '', name: '' }
  })

  const handleSave = () => {
    onSave({
      key: fieldKey,
      group: groupKey,
      field: editedField
    })
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {fieldKey ? `Edit Field: ${fieldKey}` : 'Add New Field'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {!fieldKey && (
            <div>
              <Label htmlFor="field-key">Field Key</Label>
              <Input
                id="field-key"
                placeholder="e.g., order_number"
                value={fieldKey || ''}
                disabled={!!fieldKey}
              />
            </div>
          )}

          <div>
            <Label htmlFor="field-type">Field Type</Label>
            <Select
              value={editedField.type}
              onValueChange={(value) => 
                setEditedField({ ...editedField, type: value })
              }
            >
              <SelectTrigger id="field-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="string">String</SelectItem>
                <SelectItem value="integer">Integer</SelectItem>
                <SelectItem value="boolean">Boolean</SelectItem>
                <SelectItem value="datetime">DateTime</SelectItem>
                <SelectItem value="status">Status</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="required"
              checked={editedField.required}
              onCheckedChange={(checked) =>
                setEditedField({ ...editedField, required: checked })
              }
            />
            <Label htmlFor="required">Required Field</Label>
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Field description..."
              value={editedField.description || ''}
              onChange={(e) =>
                setEditedField({ ...editedField, description: e.target.value })
              }
              rows={3}
            />
          </div>

          <div className="space-y-4">
            <h4 className="font-medium">Instance Mappings</h4>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Instance 1</Label>
                  <FieldPreview
                    fieldId={editedField.instance_1?.field_id || ''}
                    instance="instance_1"
                    fieldName={editedField.instance_1?.name}
                    disabled={!editedField.instance_1?.field_id}
                  />
                </div>
                <FieldSearchInput
                  value={editedField.instance_1?.field_id || ''}
                  onChange={(fieldId) => {
                    // Find the field in cached data to get its name
                    const fields = cachedFields?.fields?.instance_1 || { system: [], custom: [] }
                    const allFields = [...fields.system, ...fields.custom]
                    const selectedField = allFields.find((f: any) => f.field_id === fieldId)
                    
                    setEditedField({
                      ...editedField,
                      instance_1: {
                        field_id: fieldId,
                        name: selectedField?.field_name || editedField.instance_1?.name || ''
                      }
                    })
                  }}
                  instance="instance_1"
                  cachedFields={cachedFields}
                  existingMappings={existingMappings}
                />
                <Input
                  placeholder="Field Name"
                  value={editedField.instance_1?.name || ''}
                  onChange={(e) =>
                    setEditedField({
                      ...editedField,
                      instance_1: {
                        ...editedField.instance_1,
                        name: e.target.value
                      }
                    })
                  }
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Instance 2</Label>
                  <FieldPreview
                    fieldId={editedField.instance_2?.field_id || ''}
                    instance="instance_2"
                    fieldName={editedField.instance_2?.name}
                    disabled={!editedField.instance_2?.field_id}
                  />
                </div>
                <FieldSearchInput
                  value={editedField.instance_2?.field_id || ''}
                  onChange={(fieldId) => {
                    // Find the field in cached data to get its name
                    const fields = cachedFields?.fields?.instance_2 || { system: [], custom: [] }
                    const allFields = [...fields.system, ...fields.custom]
                    const selectedField = allFields.find((f: any) => f.field_id === fieldId)
                    
                    setEditedField({
                      ...editedField,
                      instance_2: {
                        field_id: fieldId,
                        name: selectedField?.field_name || editedField.instance_2?.name || ''
                      }
                    })
                  }}
                  instance="instance_2"
                  cachedFields={cachedFields}
                  existingMappings={existingMappings}
                />
                <Input
                  placeholder="Field Name"
                  value={editedField.instance_2?.name || ''}
                  onChange={(e) =>
                    setEditedField({
                      ...editedField,
                      instance_2: {
                        ...editedField.instance_2,
                        name: e.target.value
                      }
                    })
                  }
                />
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}