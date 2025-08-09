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
    } catch (error) {
      console.error('Failed to fetch status:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
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
    }
  }

  const fetchIssueCount = async () => {
    try {
      const response = await fetch('/api/admin/issues/count', {
        headers: {
          'x-admin-key': 'jira-admin-key-2024'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setIssueCount(data.total_issues)
      }
    } catch (error) {
      console.error('Failed to fetch issue count:', error)
    }
  }

  const handleClearTable = async () => {
    setClearing(true)
    try {
      const response = await fetch('/api/admin/clear-issues-table', {
        method: 'DELETE',
        headers: {
          'x-admin-key': 'jira-admin-key-2024',
          'x-user': 'dashboard-user'
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        toast({
          title: "Table Cleared Successfully",
          description: `Deleted ${data.records_deleted} records from jira_issues_v2 table`,
        })
        setIssueCount(0)
        fetchStatus() // Refresh the dashboard
      } else {
        const error = await response.text()
        toast({
          title: "Failed to Clear Table",
          description: error || "An error occurred while clearing the table",
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Failed to clear table:', error)
      toast({
        title: "Error",
        description: "Failed to connect to the server",
        variant: "destructive"
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

  const getSyncStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      idle: 'secondary',
      running: 'default',
      stopped: 'outline',
      failed: 'destructive',
    }
    return <Badge variant={variants[status] || 'secondary'}>{status?.toUpperCase() || 'UNKNOWN'}</Badge>
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
                Sync Status
              </CardTitle>
              <CardDescription>Current synchronization state</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Status</span>
                  {status && getSyncStatusBadge(status.sync_status)}
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
              <Button
                onClick={handleOpenClearDialog}
                variant="outline"
                className="flex items-center gap-2 border-red-200 hover:bg-red-50 hover:text-red-600"
                disabled={clearing || syncing}
              >
                <Trash2 className="w-4 h-4" />
                Clear Data
              </Button>
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