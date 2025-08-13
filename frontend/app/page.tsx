'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Play, Square, RefreshCw, Activity, Database, TrendingUp, Clock, Trash2, AlertTriangle } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useToast } from '@/hooks/use-toast'
import { adminFetch, checkAdminAuth } from '@/lib/admin-api'
import DashboardLayout from './dashboard-layout'

interface SystemStatus {
  sync_status: string
  sync_progress?: {
    progress_percentage: number
    current_project: number
    total_projects: number
    current_issues: number
  }
  last_sync?: {
    started_at: string
    completed_at?: string
    total_issues: number
    status: string
  }
  next_sync_time?: string
  database_connected: boolean
  system_health: string
  scheduler_info?: {
    enabled: boolean
    is_running: boolean
    interval_minutes: number
    next_run_time?: string
  }
}

interface SyncStatsSummary {
  total_syncs: number
  successful_syncs: number
  failed_syncs: number
  success_rate: number
  total_issues_processed: number
  average_duration_seconds: number
}

export default function Dashboard() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [statsSummary, setStatsSummary] = useState<SyncStatsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [clearDialogOpen, setClearDialogOpen] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [issueCount, setIssueCount] = useState<number | null>(null)
  const [isAdmin, setIsAdmin] = useState(false)
  const { toast } = useToast()

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/status/system')
      const data = await response.json()
      setStatus(data)
      setSyncing(data.sync_status === 'running')

      // Fetch stats summary
      const statsResponse = await fetch('/api/sync/stats/summary')
      if (statsResponse.ok) {
        const statsData = await statsResponse.json()
        setStatsSummary(statsData)
      }
      
      // Scheduler info now comes from system status endpoint
    } catch (error) {
      console.error('Failed to fetch status:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch system status',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    checkAdminAuth().then(setIsAdmin)
    const interval = setInterval(fetchStatus, 5000) // Poll every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const handleStartSync = async () => {
    try {
      const response = await fetch('/api/sync/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ force: false }),
      })
      if (response.ok) {
        setSyncing(true)
        fetchStatus()
      }
    } catch (error) {
      console.error('Failed to start sync:', error)
      toast({
        title: 'Error',
        description: 'Failed to start sync',
        variant: 'destructive'
      })
    }
  }

  const handleStopSync = async () => {
    try {
      const response = await fetch('/api/sync/stop', {
        method: 'POST',
      })
      if (response.ok) {
        setSyncing(false)
        fetchStatus()
      }
    } catch (error) {
      console.error('Failed to stop sync:', error)
      toast({
        title: 'Error',
        description: 'Failed to stop sync',
        variant: 'destructive'
      })
    }
  }

  const fetchIssueCount = async () => {
    try {
      const response = await adminFetch('/api/admin/issues/count')
      if (response.ok) {
        const data = await response.json()
        setIssueCount(data.total_issues)
      }
    } catch (error) {
      console.error('Failed to fetch issue count:', error)
    }
  }

  const handleClearTable = async () => {
    if (!isAdmin) {
      toast({
        title: "Admin Access Required",
        description: "This function is only available for authenticated admins",
        variant: "destructive"
      })
      setClearDialogOpen(false)
      return
    }

    setClearing(true)
    try {
      const response = await adminFetch('/api/admin/clear-issues-table', {
        method: 'DELETE'
      })
      if (response.ok) {
        toast({
          title: 'Data Cleared',
          description: 'All synced data has been removed.'
        })
        fetchStatus()
      } else {
        const data = await response.json().catch(() => null)
        toast({
          title: 'Error',
          description: data?.detail || 'Failed to clear data',
          variant: 'destructive'
        })
      }
    } catch (error) {
      console.error('Failed to clear table:', error)
      toast({
        title: 'Error',
        description: 'Failed to clear data',
        variant: 'destructive'
      })
    } finally {
      setClearing(false)
      setClearDialogOpen(false)
    }
  }

  const handleOpenClearDialog = async () => {
    // Fetch current issue count before showing dialog
    await fetchIssueCount()
    setClearDialogOpen(true)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500'
      case 'degraded':
        return 'bg-yellow-500'
      case 'failed':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const formatNextSyncTime = (time: string | null) => {
    if (!time) return "Not scheduled"
    const nextRun = new Date(time)
    const now = new Date()
    const diffMs = nextRun.getTime() - now.getTime()
    const diffMins = Math.round(diffMs / 60000)
    
    if (diffMins < 0) return "Overdue"
    if (diffMins === 0) return "Any moment"
    if (diffMins === 1) return "In 1 minute"
    if (diffMins < 60) return `In ${diffMins} minutes`
    
    const diffHours = Math.round(diffMins / 60)
    return `In ${diffHours} hour${diffHours > 1 ? 's' : ''}`
  }


  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* System Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                System Status
              </CardTitle>
              <CardDescription>Overall system health and connectivity</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">System Health</span>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(status?.system_health || 'unknown')}`}></div>
                    <span className="text-sm capitalize">{status?.system_health || 'Unknown'}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Database</span>
                  <Badge variant={status?.database_connected ? 'default' : 'destructive'}>
                    {status?.database_connected ? 'Connected' : 'Disconnected'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Sync Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <RefreshCw className="w-5 h-5" />
                Current Sync Operation
              </CardTitle>
              <CardDescription>Real-time synchronization activity</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Sync Activity</span>
                  {status && (
                    <Badge variant={status.sync_status === 'running' ? 'default' : 'secondary'}>
                      {status.sync_status === 'running' ? 'Syncing Now' : 
                       status.sync_status === 'idle' ? 'No Active Sync' : 
                       status.sync_status === 'stopped' ? 'Stopped' : 
                       status.sync_status === 'failed' ? 'Last Sync Failed' : status.sync_status}
                    </Badge>
                  )}
                </div>
                {status?.sync_progress && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Progress</span>
                      <span>{status.sync_progress.progress_percentage.toFixed(1)}%</span>
                    </div>
                    <Progress value={status.sync_progress.progress_percentage} />
                    <div className="text-xs text-muted-foreground">
                      {status.sync_progress.current_issues} issues processed
                    </div>
                  </div>
                )}
                {/* Show scheduler info when no sync is running */}
                {status?.sync_status !== 'running' && status?.scheduler_info && (
                  <div className="pt-2 border-t">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Auto-Sync</span>
                      <Badge variant={status.scheduler_info.enabled ? 'outline' : 'secondary'}>
                        {status.scheduler_info.enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    {status.scheduler_info.enabled && status.scheduler_info.next_run_time && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        Next sync: {formatNextSyncTime(status.scheduler_info.next_run_time)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Last Sync Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                Last Sync
              </CardTitle>
              <CardDescription>Previous synchronization details</CardDescription>
            </CardHeader>
            <CardContent>
              {status?.last_sync ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Status</span>
                    <Badge variant={status.last_sync.status === 'completed' ? 'default' : 'destructive'}>
                      {status.last_sync.status}
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <div>Started: {new Date(status.last_sync.started_at).toLocaleString()}</div>
                    <div>Issues: {status.last_sync.total_issues}</div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No sync history available</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sync Statistics Summary */}
        {statsSummary && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Sync Statistics (Last 7 Days)
              </CardTitle>
              <CardDescription>Performance and success metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Syncs</p>
                  <p className="text-2xl font-bold">{statsSummary.total_syncs}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Success Rate</p>
                  <p className="text-2xl font-bold text-green-600">{statsSummary.success_rate}%</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Issues Processed</p>
                  <p className="text-2xl font-bold">{statsSummary.total_issues_processed.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Successful</p>
                  <p className="text-2xl font-bold">{statsSummary.successful_syncs}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Failed</p>
                  <p className="text-2xl font-bold text-red-600">{statsSummary.failed_syncs}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Avg Duration</p>
                  <p className="text-2xl font-bold">
                    {Math.floor(statsSummary.average_duration_seconds / 60)}m
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Sync Control */}
        <Card>
          <CardHeader>
            <CardTitle>Sync Control</CardTitle>
            <CardDescription>Manually control synchronization operations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Button
                onClick={handleStartSync}
                disabled={syncing}
                className="flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Start Sync
              </Button>
              <Button
                onClick={handleStopSync}
                disabled={!syncing}
                variant="destructive"
                className="flex items-center gap-2"
              >
                <Square className="w-4 h-4" />
                Stop Sync
              </Button>
              <Button
                onClick={fetchStatus}
                variant="outline"
                className="flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </Button>
              {isAdmin && (
                <Button
                  onClick={handleOpenClearDialog}
                  variant="outline"
                  className="flex items-center gap-2 border-red-200 hover:bg-red-50 hover:text-red-600"
                  disabled={clearing || syncing}
                >
                  <Trash2 className="w-4 h-4" />
                  Clear Data
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Clear Table Confirmation Dialog */}
      <AlertDialog open={clearDialogOpen} onOpenChange={setClearDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              Clear All Synced Data?
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-2">
                <div>
                  This action will permanently delete all synced issues from the jira_issues_v2 table.
                </div>
                {issueCount !== null && issueCount > 0 && (
                  <div className="font-semibold text-red-600">
                    Warning: This will delete {issueCount.toLocaleString()} records!
                  </div>
                )}
                <div>
                  This is useful for testing that your field mappings are working correctly with a fresh sync.
                </div>
                <div className="text-sm text-muted-foreground">
                  Note: This only clears the local database. JIRA data remains unchanged.
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={clearing}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleClearTable}
              disabled={clearing}
              className="bg-red-600 hover:bg-red-700"
            >
              {clearing ? 'Clearing...' : 'Clear All Data'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DashboardLayout>
  )
}