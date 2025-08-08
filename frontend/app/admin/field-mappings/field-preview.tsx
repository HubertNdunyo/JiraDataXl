'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Eye, Loader2, AlertCircle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface FieldPreviewProps {
  fieldId: string
  instance: 'instance_1' | 'instance_2'
  fieldName?: string
  disabled?: boolean
}

interface PreviewData {
  field_id: string
  instance: string
  field_info: any
  sample_count: number
  samples: Array<{
    issue_key: string
    value: string
    raw_value: string
  }>
}

export function FieldPreview({ fieldId, instance, fieldName, disabled }: FieldPreviewProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)

  const fetchPreview = async () => {
    if (!fieldId) return

    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(
        `/api/admin/fields/preview?field_id=${encodeURIComponent(fieldId)}&instance=${instance}&limit=5`,
        {
          method: 'POST',
          headers: {
            'X-Admin-Key': 'jira-admin-key-2024'
          }
        }
      )

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Failed to fetch preview')
      }

      const data = await response.json()
      setPreviewData(data)
      setIsOpen(true)
      
      // Show error if present
      if (data.error) {
        setError(data.error)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
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
    <>
      <Button
        size="sm"
        variant="ghost"
        onClick={fetchPreview}
        disabled={disabled || !fieldId || loading}
        className="h-8"
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Eye className="w-4 h-4" />
        )}
        <span className="ml-2">Preview</span>
      </Button>

      {error && (
        <Alert variant="destructive" className="mt-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Field Preview: {fieldName || fieldId}
            </DialogTitle>
          </DialogHeader>

          {previewData && (
            <div className="space-y-4">
              {/* Show error if present */}
              {previewData.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{previewData.error}</AlertDescription>
                </Alert>
              )}
              
              {/* Field Information */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium mb-2">Field Information</h3>
                <div className="space-y-1 text-sm">
                  <div>
                    <span className="font-medium">Field ID:</span> {previewData.field_id}
                  </div>
                  <div>
                    <span className="font-medium">Instance:</span> {previewData.instance.replace('_', ' ')}
                  </div>
                  {previewData.field_info && (
                    <div className="flex items-center gap-2">
                      <span className="font-medium">Type:</span>
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${getFieldTypeColor(previewData.field_info.field_type)}`}
                      >
                        {previewData.field_info.field_type}
                      </Badge>
                      {previewData.field_info.is_array && (
                        <Badge variant="secondary" className="text-xs">
                          Array
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Sample Values */}
              <div>
                <h3 className="font-medium mb-2">
                  Sample Values ({previewData.sample_count} found)
                </h3>
                {previewData.samples.length > 0 ? (
                  <div className="space-y-2">
                    {previewData.samples.map((sample, index) => (
                      <div 
                        key={index} 
                        className="border rounded p-3 bg-white"
                      >
                        <div className="flex justify-between items-start mb-1">
                          <span className="text-sm text-gray-600">
                            Issue: {sample.issue_key}
                          </span>
                        </div>
                        <div className="font-mono text-sm bg-gray-100 p-2 rounded">
                          {sample.value}
                        </div>
                        {sample.value !== sample.raw_value && (
                          <details className="mt-2">
                            <summary className="text-xs text-gray-500 cursor-pointer">
                              Show raw value
                            </summary>
                            <div className="mt-1 text-xs font-mono bg-gray-50 p-2 rounded overflow-x-auto">
                              {sample.raw_value}
                            </div>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      No issues found with values for this field. The field might be empty in all issues.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}