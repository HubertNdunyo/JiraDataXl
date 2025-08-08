'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Play, 
  Plus, 
  Trash2, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle,
  ArrowRight,
  Camera,
  Upload,
  Edit,
  Eye,
  XCircle
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import DashboardLayout from '../../dashboard-layout'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { useToast } from '@/hooks/use-toast'

interface IssueData {
  key: string
  summary: string
  status: string
  status_category: string
  created: string
  url: string
  transitions: Array<{
    id: string
    name: string
    to: string
  }>
}

interface WorkflowStep {
  status: string
  order: number
  initial?: boolean
  final?: boolean
  alternate?: boolean
  requires_field?: string
}

const statusIcons: Record<string, any> = {
  'Scheduled': Play,
  'ACKNOWLEDGED': CheckCircle,
  'At Listing': Camera,
  'Shoot Complete': Camera,
  'Uploaded': Upload,
  'Edit': Edit,
  'Final Review': Eye,
  'Closed': CheckCircle,
  'Escalated Editing': AlertCircle
}

export default function INUATestPage() {
  const [activeIssue, setActiveIssue] = useState<IssueData | null>(null)
  const [issueSummary, setIssueSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [fieldDialogOpen, setFieldDialogOpen] = useState(false)
  const [fieldValue, setFieldValue] = useState('')
  const [pendingTransition, setPendingTransition] = useState<any>(null)
  const [workflowInfo, setWorkflowInfo] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    fetchWorkflowInfo()
  }, [])

  const fetchWorkflowInfo = async () => {
    try {
      const response = await axios.get(`${apiUrl}/api/admin/inua-test/workflow-info`)
      setWorkflowInfo(response.data)
    } catch (err) {
      console.error('Failed to fetch workflow info:', err)
    }
  }

  const createIssue = async () => {
    if (!issueSummary.trim()) {
      setError('Please enter a summary for the test card')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${apiUrl}/api/admin/inua-test/create-issue`, {
        summary: issueSummary
      })
      
      setActiveIssue(response.data)
      setIssueSummary('')
      toast({
        title: 'Success',
        description: `Created test card: ${response.data.key}`,
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create issue')
      toast({
        title: 'Error',
        description: 'Failed to create test card',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const refreshIssue = async () => {
    if (!activeIssue) return

    setLoading(true)
    try {
      const response = await axios.get(`${apiUrl}/api/admin/inua-test/issue/${activeIssue.key}`)
      setActiveIssue(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to refresh issue')
    } finally {
      setLoading(false)
    }
  }

  const deleteIssue = async () => {
    if (!activeIssue) return

    if (!confirm(`Delete test card ${activeIssue.key}?`)) return

    setLoading(true)
    try {
      await axios.delete(`${apiUrl}/api/admin/inua-test/issue/${activeIssue.key}`)
      setActiveIssue(null)
      toast({
        title: 'Success',
        description: 'Test card deleted',
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete issue')
      toast({
        title: 'Error',
        description: 'Failed to delete test card',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleTransition = async (targetStatus: string) => {
    if (!activeIssue) return

    // Check if this transition requires a field
    const workflowStep = workflowInfo?.workflow.find((w: WorkflowStep) => w.status === targetStatus)
    if (workflowStep?.requires_field) {
      setPendingTransition({ targetStatus, fieldId: workflowStep.requires_field })
      setFieldDialogOpen(true)
      return
    }

    performTransition(targetStatus)
  }

  const performTransition = async (targetStatus: string, fieldUpdates?: any) => {
    if (!activeIssue) return

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${apiUrl}/api/admin/inua-test/transition`, {
        issue_key: activeIssue.key,
        target_status: targetStatus,
        comment: `Transitioning to ${targetStatus} via INUA Test Dashboard`,
        field_updates: fieldUpdates
      })

      if (response.data.success) {
        await refreshIssue()
        toast({
          title: 'Success',
          description: response.data.message,
        })
      } else {
        setError(response.data.message)
        toast({
          title: 'Error',
          description: response.data.message,
          variant: 'destructive',
        })
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to transition')
      toast({
        title: 'Error',
        description: 'Failed to transition issue',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleFieldSubmit = () => {
    if (!pendingTransition || !fieldValue.trim()) return

    const fieldUpdates = {
      [pendingTransition.fieldId]: fieldValue
    }

    performTransition(pendingTransition.targetStatus, fieldUpdates)
    setFieldDialogOpen(false)
    setFieldValue('')
    setPendingTransition(null)
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'Scheduled': 'bg-gray-500',
      'ACKNOWLEDGED': 'bg-blue-500',
      'At Listing': 'bg-yellow-500',
      'Shoot Complete': 'bg-orange-500',
      'Uploaded': 'bg-purple-500',
      'Edit': 'bg-pink-500',
      'Final Review': 'bg-indigo-500',
      'Closed': 'bg-green-500',
      'Escalated Editing': 'bg-red-500'
    }
    return colors[status] || 'bg-gray-400'
  }

  const renderWorkflowProgress = () => {
    if (!workflowInfo || !activeIssue) return null

    const mainWorkflow = workflowInfo.workflow.filter((w: WorkflowStep) => !w.alternate)
    const currentIndex = mainWorkflow.findIndex((w: WorkflowStep) => w.status === activeIssue.status)

    return (
      <div className="flex items-center justify-between mb-6">
        {mainWorkflow.map((step: WorkflowStep, index: number) => {
          const Icon = statusIcons[step.status] || Play
          const isActive = step.status === activeIssue.status
          const isPast = currentIndex > index
          
          return (
            <div key={step.status} className="flex items-center">
              <div className={`flex flex-col items-center ${
                index < mainWorkflow.length - 1 ? 'flex-1' : ''
              }`}>
                <div className={`
                  w-10 h-10 rounded-full flex items-center justify-center
                  ${isActive ? getStatusColor(step.status) + ' text-white' : 
                    isPast ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-400'}
                `}>
                  <Icon className="w-5 h-5" />
                </div>
                <span className={`text-xs mt-1 ${isActive ? 'font-semibold' : ''}`}>
                  {step.status}
                </span>
              </div>
              {index < mainWorkflow.length - 1 && (
                <div className={`h-0.5 w-full mx-2 ${
                  isPast ? 'bg-green-500' : 'bg-gray-300'
                }`} />
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-6xl">
        <h1 className="text-3xl font-bold mb-8">INUA Testing Dashboard</h1>
        
        {error && (
          <Alert className="mb-4" variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Create Card Section */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5" />
              Create Test Card
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <div className="flex-1">
                <Label htmlFor="summary">Card Summary</Label>
                <Input
                  id="summary"
                  placeholder="Enter test card description"
                  value={issueSummary}
                  onChange={(e) => setIssueSummary(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && createIssue()}
                  disabled={loading || activeIssue !== null}
                />
              </div>
              <div className="flex items-end">
                <Button 
                  onClick={createIssue} 
                  disabled={loading || activeIssue !== null}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Card
                </Button>
              </div>
            </div>
            {activeIssue && (
              <p className="text-sm text-gray-500 mt-2">
                Delete the current card to create a new one
              </p>
            )}
          </CardContent>
        </Card>

        {/* Active Card Section */}
        {activeIssue && (
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="flex items-center gap-3">
                    {activeIssue.key}
                    <Badge className={getStatusColor(activeIssue.status)}>
                      {activeIssue.status}
                    </Badge>
                  </CardTitle>
                  <p className="text-sm text-gray-500 mt-1">{activeIssue.summary}</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={refreshIssue}
                    disabled={loading}
                  >
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => window.open(activeIssue.url, '_blank')}
                  >
                    View in JIRA
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={deleteIssue}
                    disabled={loading}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Workflow Progress */}
              {renderWorkflowProgress()}

              {/* Available Transitions */}
              <div className="mt-6">
                <h3 className="text-sm font-semibold mb-3">Available Transitions</h3>
                <div className="flex flex-wrap gap-2">
                  {activeIssue.transitions.length > 0 ? (
                    activeIssue.transitions.map((transition) => (
                      <Button
                        key={transition.id}
                        onClick={() => handleTransition(transition.to)}
                        disabled={loading}
                        variant="outline"
                        size="sm"
                      >
                        <ArrowRight className="w-4 h-4 mr-2" />
                        {transition.name} → {transition.to}
                      </Button>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No transitions available from this status</p>
                  )}
                </div>
              </div>

              {/* Special Transitions */}
              {activeIssue.status === 'Shoot Complete' && (
                <Alert className="mt-4">
                  <AlertDescription>
                    💡 The "failed shoot" transition will move directly to Closed status
                  </AlertDescription>
                </Alert>
              )}

              {activeIssue.status === 'Final Review' && (
                <Alert className="mt-4">
                  <AlertDescription>
                    💡 Use "Not Approved" to escalate with revision notes
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        )}

        {/* Field Dialog */}
        <Dialog open={fieldDialogOpen} onOpenChange={setFieldDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Required Field</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>
                  {pendingTransition?.fieldId === 'customfield_12602' 
                    ? 'Number of Raw Photos' 
                    : 'Revision Notes'}
                </Label>
                {pendingTransition?.fieldId === 'customfield_12602' ? (
                  <Input
                    placeholder="e.g., 25"
                    value={fieldValue}
                    onChange={(e) => setFieldValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleFieldSubmit()}
                  />
                ) : (
                  <Textarea
                    placeholder="e.g., Photos need color correction and exposure adjustment"
                    value={fieldValue}
                    onChange={(e) => setFieldValue(e.target.value)}
                    rows={3}
                  />
                )}
                <p className="text-sm text-gray-500 mt-1">
                  This field is required for the transition
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setFieldDialogOpen(false)
                setFieldValue('')
                setPendingTransition(null)
              }}>
                Cancel
              </Button>
              <Button onClick={handleFieldSubmit} disabled={!fieldValue.trim()}>
                Continue Transition
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Instructions */}
        {!activeIssue && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>How to Use</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm">1. Create a test card with a descriptive summary</p>
              <p className="text-sm">2. Use the transition buttons to move through the workflow</p>
              <p className="text-sm">3. Some transitions require additional fields:</p>
              <ul className="ml-6 list-disc text-sm space-y-1">
                <li>Shoot Complete → Uploaded: Number of photos</li>
                <li>Final Review → Escalated Editing: Revision notes</li>
              </ul>
              <p className="text-sm">4. Delete the card when testing is complete</p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}