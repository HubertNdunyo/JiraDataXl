'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { FileJson, RefreshCw, Edit, Plus, Save, AlertCircle, CheckCircle, ShieldCheck, Search, Loader2, Wand2, Database } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { FieldEditDialog } from './edit-dialog'
import { MappingWizard } from './mapping-wizard'
import { toast } from '@/hooks/use-toast'
import { Alert, AlertDescription } from '@/components/ui/alert'
import DashboardLayout from '../../dashboard-layout'
import { adminFetch } from '@/lib/admin-api'

export default function FieldMappingsPage() {
  const [config, setConfig] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('visual')
  const [editMode, setEditMode] = useState(false)
  const [saving, setSaving] = useState(false)
  const [validating, setValidating] = useState(false)
  const [validationResults, setValidationResults] = useState<any>(null)
  const [editDialog, setEditDialog] = useState<{
    open: boolean
    field?: any
    fieldKey?: string
    groupKey?: string
  }>({ open: false })
  const [discovering, setDiscovering] = useState(false)
  const [cachedFields, setCachedFields] = useState<any>(null)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [syncingSchema, setSyncingSchema] = useState(false)

  const fetchConfig = async () => {
    setLoading(true)
    try {
      const response = await adminFetch('/api/admin/config/field-mappings')
      if (response.ok) {
        const data = await response.json()
        setConfig(data)
      } else {
        console.error('Failed to fetch config:', response.status, response.statusText)
        const errorText = await response.text()
        console.error('Error details:', errorText)
      }
    } catch (error) {
      console.error('Failed to fetch config:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    setSaving(true)
    try {
      const response = await adminFetch('/api/admin/config/field-mappings', {
        method: 'PUT',
        body: JSON.stringify(config)
      })

      if (response.ok) {
        const result = await response.json()
        toast({
          title: 'Success',
          description: 'Field mappings updated successfully'
        })
        setEditMode(false)
      } else {
        throw new Error('Failed to save configuration')
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save configuration',
        variant: 'destructive'
      })
    } finally {
      setSaving(false)
    }
  }

  const validateConfig = async () => {
    setValidating(true)
    setValidationResults(null)
    try {
      const response = await adminFetch('/api/admin/config/field-mappings/validate', {
        method: 'POST',
        body: JSON.stringify(config)
      })

      if (response.ok) {
        const results = await response.json()
        setValidationResults(results)
        
        if (results.valid) {
          toast({
            title: 'Validation Successful',
            description: 'All field mappings are valid'
          })
        } else {
          toast({
            title: 'Validation Failed',
            description: `Found ${results.errors.length} error(s)`,
            variant: 'destructive'
          })
        }
      } else {
        throw new Error('Validation request failed')
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to validate configuration',
        variant: 'destructive'
      })
    } finally {
      setValidating(false)
    }
  }

  const handleFieldEdit = (data: any) => {
    const { key, group, field } = data
    const newConfig = { ...config }
    
    if (!newConfig.field_groups[group]) {
      newConfig.field_groups[group] = { fields: {} }
    }
    
    newConfig.field_groups[group].fields[key] = field
    setConfig(newConfig)
    setEditDialog({ open: false })
  }

  const openEditDialog = (fieldKey: string, field: any, groupKey: string) => {
    setEditDialog({
      open: true,
      field,
      fieldKey,
      groupKey
    })
  }

  const handleWizardComplete = async (wizardConfig: any) => {
    // The wizard now returns the complete config structure
    setConfig(wizardConfig)
    setWizardOpen(false)
    
    // Automatically save the configuration
    setSaving(true)
    try {
      const response = await adminFetch('/api/admin/config/field-mappings', {
        method: 'PUT',
        body: JSON.stringify(wizardConfig)
      })

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Field mappings created and saved successfully'
        })
        // Refresh the config to ensure we have the latest from the server
        await fetchConfig()
      } else {
        const errorData = await response.json().catch(() => null)
        const errorMessage = errorData?.detail || 'Failed to save configuration'
        throw new Error(errorMessage)
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to save field mappings',
        variant: 'destructive'
      })
      setEditMode(true) // Enable edit mode so user can try to save manually
    } finally {
      setSaving(false)
    }
  }

  const discoverFields = async () => {
    setDiscovering(true)
    try {
      const response = await adminFetch('/api/admin/fields/discover', {
        method: 'POST'
      })
      if (response.ok) {
        const data = await response.json()
        toast({
          title: "Field Discovery Complete",
          description: `Discovered ${data.results.instance_1.discovered} fields from Instance 1 and ${data.results.instance_2.discovered} fields from Instance 2`,
        })
        // Fetch cached fields after discovery
        fetchCachedFields()
      } else {
        const error = await response.text()
        toast({
          title: "Discovery Failed",
          description: error,
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Failed to discover fields:', error)
      toast({
        title: "Discovery Failed",
        description: "Failed to connect to JIRA",
        variant: "destructive"
      })
    } finally {
      setDiscovering(false)
    }
  }

  const fetchCachedFields = async () => {
    try {
      const response = await adminFetch('/api/admin/fields/cached', {
      })
      if (response.ok) {
        const data = await response.json()
        setCachedFields(data)
      }
    } catch (error) {
      console.error('Failed to fetch cached fields:', error)
    }
  }

  const getExistingMappings = () => {
    const mappings: string[] = []
    if (!config || !config.field_groups) return mappings

    Object.values(config.field_groups).forEach((group: any) => {
      Object.values(group.fields || {}).forEach((field: any) => {
        if (field.instance_1?.field_id) {
          mappings.push(field.instance_1.field_id)
        }
        if (field.instance_2?.field_id) {
          mappings.push(field.instance_2.field_id)
        }
      })
    })
    
    return mappings
  }

  const syncDatabaseSchema = async () => {
    setSyncingSchema(true)
    try {
      const response = await adminFetch('/api/admin/schema/sync', {
        method: 'POST'
      })
      
      if (response.ok) {
        const result = await response.json()
        
        if (result.added_columns.length > 0) {
          toast({
            title: 'Schema Updated',
            description: `Added ${result.added_columns.length} new columns: ${result.added_columns.join(', ')}`
          })
        } else {
          toast({
            title: 'Schema Up to Date',
            description: 'All configured fields already have database columns'
          })
        }
        
        if (result.errors.length > 0) {
          toast({
            title: 'Some Errors Occurred',
            description: result.errors.join(', '),
            variant: 'destructive'
          })
        }
      } else {
        throw new Error('Failed to sync schema')
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to sync database schema',
        variant: 'destructive'
      })
    } finally {
      setSyncingSchema(false)
    }
  }

  useEffect(() => {
    fetchConfig()
    fetchCachedFields()
  }, [])

  if (loading) {
    return <div className="flex items-center justify-center h-64">
      <div className="text-lg">Loading...</div>
    </div>
  }

  if (!config) {
    return <div className="flex items-center justify-center h-64">
      <div className="text-lg text-red-600">Failed to load configuration</div>
    </div>
  }

  return (
    <DashboardLayout>
      <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Field Mappings</h1>
        <div className="flex gap-2">
          {editMode ? (
            <>
              <Button 
                onClick={() => setEditMode(false)} 
                variant="outline" 
                size="sm"
                disabled={saving}
              >
                Cancel
              </Button>
              <Button 
                onClick={saveConfig} 
                size="sm"
                disabled={saving}
              >
                <Save className="w-4 h-4 mr-2" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </>
          ) : (
            <>
              <Button 
                onClick={() => setWizardOpen(true)} 
                size="sm"
                variant="default"
              >
                <Wand2 className="w-4 h-4 mr-2" />
                Setup Wizard
              </Button>
              <Button 
                onClick={() => setEditMode(true)} 
                size="sm"
                variant="outline"
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit Mode
              </Button>
              <Button 
                onClick={validateConfig} 
                variant="outline" 
                size="sm"
                disabled={validating}
              >
                <ShieldCheck className={`w-4 h-4 mr-2 ${validating ? 'animate-spin' : ''}`} />
                {validating ? 'Validating...' : 'Validate'}
              </Button>
              <Button onClick={fetchConfig} variant="outline" size="sm">
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button 
                onClick={discoverFields} 
                variant="outline" 
                size="sm"
                disabled={discovering}
              >
                {discovering ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Search className="w-4 h-4 mr-2" />
                )}
                {discovering ? 'Discovering...' : 'Discover Fields'}
              </Button>
              <Button 
                onClick={syncDatabaseSchema} 
                variant="outline" 
                size="sm"
                disabled={syncingSchema}
              >
                {syncingSchema ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Database className="w-4 h-4 mr-2" />
                )}
                {syncingSchema ? 'Syncing...' : 'Sync DB Schema'}
              </Button>
            </>
          )}
        </div>
      </div>

      {validationResults && (
        <Alert className={`mb-6 ${validationResults.valid ? '' : 'border-red-500'}`}>
          <div className="flex items-start gap-2">
            {validationResults.valid ? (
              <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
            )}
            <div className="flex-1">
              <AlertDescription>
                <div className="font-semibold mb-2">
                  {validationResults.valid ? 'Validation Passed' : 'Validation Failed'}
                </div>
                {validationResults.errors && validationResults.errors.length > 0 && (
                  <div className="mb-3">
                    <div className="text-sm font-medium text-red-600 mb-1">Errors:</div>
                    <ul className="list-disc list-inside space-y-1">
                      {validationResults.errors.map((error: string, index: number) => (
                        <li key={index} className="text-sm text-red-600">{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {validationResults.warnings && validationResults.warnings.length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-amber-600 mb-1">Warnings:</div>
                    <ul className="list-disc list-inside space-y-1">
                      {validationResults.warnings.map((warning: string, index: number) => (
                        <li key={index} className="text-sm text-amber-600">{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </AlertDescription>
            </div>
          </div>
        </Alert>
      )}

      {cachedFields && cachedFields.stats && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              Field Discovery Stats
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">Instance 1</h4>
                {cachedFields.stats.instance_1 ? (
                  <div className="text-sm space-y-1">
                    <p>Total Fields: {cachedFields.stats.instance_1.total_fields}</p>
                    <p>Custom Fields: {cachedFields.stats.instance_1.custom_fields}</p>
                    <p>System Fields: {cachedFields.stats.instance_1.system_fields}</p>
                    <p className="text-gray-500">
                      Last Updated: {new Date(cachedFields.stats.instance_1.last_updated).toLocaleString()}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No fields discovered yet</p>
                )}
              </div>
              <div>
                <h4 className="font-medium mb-2">Instance 2</h4>
                {cachedFields.stats.instance_2 ? (
                  <div className="text-sm space-y-1">
                    <p>Total Fields: {cachedFields.stats.instance_2.total_fields}</p>
                    <p>Custom Fields: {cachedFields.stats.instance_2.custom_fields}</p>
                    <p>System Fields: {cachedFields.stats.instance_2.system_fields}</p>
                    <p className="text-gray-500">
                      Last Updated: {new Date(cachedFields.stats.instance_2.last_updated).toLocaleString()}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No fields discovered yet</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="visual">Visual View</TabsTrigger>
          <TabsTrigger value="json">JSON View</TabsTrigger>
        </TabsList>

        <TabsContent value="visual" className="mt-6">
          <div className="space-y-6">
            {config && Object.entries(config.field_groups || {}).map(([groupKey, group]: [string, any]) => (
              <Card key={groupKey}>
                <CardHeader>
                  <CardTitle className="text-lg">{groupKey}</CardTitle>
                  <p className="text-sm text-gray-600">{group.description}</p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(group.fields || {}).map(([fieldKey, field]: [string, any]) => (
                      <div key={fieldKey} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-medium">{fieldKey}</h4>
                          <div className="flex gap-2">
                            {editMode && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => openEditDialog(fieldKey, field, groupKey)}
                              >
                                <Edit className="w-3 h-3" />
                              </Button>
                            )}
                            <Badge variant="outline">{field.type}</Badge>
                            {field.required && <Badge variant="destructive">Required</Badge>}
                          </div>
                        </div>
                        {field.description && (
                          <p className="text-sm text-gray-600 mb-3">{field.description}</p>
                        )}
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="font-medium">Instance 1:</p>
                            <p className="text-gray-600">{field.instance_1?.field_id || 'Not mapped'}</p>
                            {field.instance_1?.name && (
                              <p className="text-xs text-gray-500">{field.instance_1.name}</p>
                            )}
                          </div>
                          <div>
                            <p className="font-medium">Instance 2:</p>
                            <p className="text-gray-600">{field.instance_2?.field_id || 'Not mapped'}</p>
                            {field.instance_2?.name && (
                              <p className="text-xs text-gray-500">{field.instance_2.name}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="json" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileJson className="w-5 h-5" />
                Raw Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="max-h-[600px] overflow-auto">
                <SyntaxHighlighter 
                  language="json" 
                  style={tomorrow}
                  customStyle={{
                    margin: 0,
                    borderRadius: '0.5rem'
                  }}
                >
                  {JSON.stringify(config, null, 2)}
                </SyntaxHighlighter>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {editMode && (
        <Alert className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            You are in edit mode. Click on the edit icon next to any field to modify it.
            Remember to save your changes when done.
          </AlertDescription>
        </Alert>
      )}

      <FieldEditDialog
        open={editDialog.open}
        onClose={() => setEditDialog({ open: false })}
        onSave={handleFieldEdit}
        field={editDialog.field}
        fieldKey={editDialog.fieldKey}
        groupKey={editDialog.groupKey}
        cachedFields={cachedFields}
        existingMappings={getExistingMappings()}
      />

      <MappingWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onComplete={handleWizardComplete}
        cachedFields={cachedFields}
        existingConfig={config}
      />
      </div>
    </DashboardLayout>
  )
}