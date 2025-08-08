'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  TrendingUp,
  Activity,
  Zap,
  AlertTriangle
} from 'lucide-react'

interface SyncDetailModalProps {
  open: boolean
  onClose: () => void
  syncId: string | null
}

interface ProjectDetail {
  project_key: string
  instance: string
  started_at: string
  completed_at?: string
  duration_seconds?: number
  status: string
  issues_processed: number
  issues_created: number
  issues_updated: number
  issues_failed: number
  error_message?: string
}

export function SyncDetailModal({ open, onClose, syncId }: SyncDetailModalProps) {
  const [loading, setLoading] = useState(false)
  const [syncDetails, setSyncDetails] = useState<any>(null)
  const [projectDetails, setProjectDetails] = useState<ProjectDetail[]>([])
  const [metrics, setMetrics] = useState<any>({})

  useEffect(() => {
    if (open && syncId) {
      fetchSyncDetails()
    }
  }, [open, syncId])

  const fetchSyncDetails = async () => {
    if (!syncId) return
    
    setLoading(true)
    try {
      // Fetch sync details
      const statsRes = await fetch(`/api/sync/stats/${syncId}`)
      if (statsRes.ok) {
        const stats = await statsRes.json()
        setSyncDetails(stats)
      }

      // Fetch project details
      const projectsRes = await fetch(`/api/sync/history/${syncId}/projects`)
      if (projectsRes.ok) {
        const data = await projectsRes.json()
        setProjectDetails(data.projects || [])
      }

      // Fetch performance metrics
      const metricsRes = await fetch(`/api/sync/history/${syncId}/metrics`)
      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics(data.metrics || {})
      }
    } catch (error) {
      console.error('Failed to fetch sync details:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs.toFixed(0)}s`
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'running':
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />
      case 'skipped':
        return <AlertCircle className="w-4 h-4 text-gray-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'completed':
        return 'default'
      case 'failed':
        return 'destructive'
      case 'running':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  if (!open) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Sync Operation Details</DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : syncDetails ? (
          <Tabs defaultValue="overview" className="mt-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="projects">Projects</TabsTrigger>
              <TabsTrigger value="metrics">Metrics</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(syncDetails.status)}
                      <Badge variant={getStatusBadgeVariant(syncDetails.status)}>
                        {syncDetails.status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Duration</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span>{formatDuration(syncDetails.duration_seconds)}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Projects</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Successful</span>
                        <span className="font-medium">{syncDetails.successful_projects}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Failed</span>
                        <span className="font-medium">{syncDetails.failed_projects}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Total</span>
                        <span className="font-medium">{syncDetails.total_projects}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">Issues</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Processed</span>
                        <span className="font-medium">{syncDetails.total_issues}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Speed</span>
                        <span className="font-medium">
                          {syncDetails.issues_per_second?.toFixed(1) || 0} issues/sec
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {syncDetails.error_message && (
                <Card className="border-red-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-red-500">
                      <AlertTriangle className="w-4 h-4 inline mr-2" />
                      Error Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-red-600">{syncDetails.error_message}</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="projects">
              <div className="h-[400px] overflow-y-auto">
                <div className="space-y-2">
                  {projectDetails.map((project) => (
                    <Card key={`${project.project_key}-${project.instance}`}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(project.status)}
                            <span className="font-medium">{project.project_key}</span>
                            <Badge variant="outline" className="text-xs">
                              {project.instance}
                            </Badge>
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {formatDuration(project.duration_seconds)}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-4 gap-2 text-sm">
                          <div>
                            <span className="text-muted-foreground">Processed:</span>
                            <span className="ml-1 font-medium">{project.issues_processed}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Created:</span>
                            <span className="ml-1 font-medium">{project.issues_created}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Updated:</span>
                            <span className="ml-1 font-medium">{project.issues_updated}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Failed:</span>
                            <span className="ml-1 font-medium">{project.issues_failed}</span>
                          </div>
                        </div>

                        {project.error_message && (
                          <div className="mt-2 p-2 bg-red-50 rounded text-sm text-red-600">
                            {project.error_message}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                  
                  {projectDetails.length === 0 && (
                    <p className="text-center text-muted-foreground py-8">
                      No project details available
                    </p>
                  )}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="metrics">
              <div className="space-y-4">
                {Object.entries(metrics).map(([metricName, values]: [string, any]) => (
                  <Card key={metricName}>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium">
                        {metricName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {Array.isArray(values) && values.map((metric, idx) => (
                        <div key={idx} className="flex justify-between items-center py-1">
                          <span className="text-sm">
                            {metric.value.toFixed(2)} {metric.unit}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(metric.recorded_at).toLocaleTimeString()}
                          </span>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                ))}
                
                {Object.keys(metrics).length === 0 && (
                  <p className="text-center text-muted-foreground py-8">
                    No performance metrics available
                  </p>
                )}
              </div>
            </TabsContent>
          </Tabs>
        ) : (
          <p className="text-center text-muted-foreground py-8">
            Failed to load sync details
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}