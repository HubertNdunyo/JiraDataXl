'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Clock, CheckCircle, XCircle, AlertCircle, ChevronLeft, ChevronRight, RefreshCw, Eye } from 'lucide-react'
import DashboardLayout from '../dashboard-layout'
import { SyncDetailModal } from './sync-detail-modal'
import { toast } from '@/hooks/use-toast'

interface SyncHistory {
  sync_id: string
  started_at: string
  completed_at?: string
  duration_seconds?: number
  total_projects: number
  successful_projects: number
  failed_projects: number
  total_issues: number
  status: string
}

export default function HistoryPage() {
  const [history, setHistory] = useState<SyncHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [refreshing, setRefreshing] = useState(false)
  const [selectedSyncId, setSelectedSyncId] = useState<string | null>(null)
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const limit = 10

  useEffect(() => {
    fetchHistory()
  }, [page, statusFilter])

  const fetchHistory = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: (page * limit).toString()
      })
      
      if (statusFilter !== 'all') {
        params.append('status', statusFilter)
      }

      const response = await fetch(`/api/sync/history?${params}`)
      const data = await response.json()
      setHistory(data.items || [])
      setTotal(data.total || 0)
    } catch (error) {
      console.error('Failed to fetch history:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch sync history',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchHistory()
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'stopped':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'running':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />
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

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs.toFixed(0)}s`
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Sync History</CardTitle>
                <CardDescription>View past sync operations and their results</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Select value={statusFilter} onValueChange={(value) => { setStatusFilter(value); setPage(0); }}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="stopped">Stopped</SelectItem>
                    <SelectItem value="running">Running</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={refreshing}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {history.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">No sync history available</p>
            ) : (
              <div className="space-y-4">
                {history.map((sync) => (
                  <div
                    key={sync.sync_id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      {getStatusIcon(sync.status)}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {new Date(sync.started_at).toLocaleString()}
                          </span>
                          <Badge variant={getStatusBadgeVariant(sync.status)}>
                            {sync.status}
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          Duration: {formatDuration(sync.duration_seconds)} • 
                          Issues: {sync.total_issues} • 
                          Projects: {sync.successful_projects}/{sync.total_projects}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedSyncId(sync.sync_id)
                          setDetailModalOpen(true)
                        }}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Details
                      </Button>
                      <span className="text-sm text-muted-foreground">
                        {sync.sync_id.slice(0, 8)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {/* Pagination controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-6 border-t">
                <div className="text-sm text-muted-foreground">
                  Showing {page * limit + 1} to {Math.min((page + 1) * limit, total)} of {total} syncs
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page - 1)}
                    disabled={page === 0}
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground px-2">
                    Page {page + 1} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page + 1)}
                    disabled={page >= totalPages - 1}
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      <SyncDetailModal
        open={detailModalOpen}
        onClose={() => {
          setDetailModalOpen(false)
          setSelectedSyncId(null)
        }}
        syncId={selectedSyncId}
      />
    </DashboardLayout>
  )
}