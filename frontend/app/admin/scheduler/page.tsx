"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import { Clock, RefreshCw, Settings } from "lucide-react"
import DashboardLayout from "../../dashboard-layout"
import { adminFetch } from "@/lib/admin-api"

interface SchedulerStatus {
  enabled: boolean
  interval_minutes: number
  is_running: boolean
  next_run_time: string | null
}

export default function SchedulerPage() {
  const [status, setStatus] = useState<SchedulerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [intervalValue, setIntervalValue] = useState([30])
  const [enabled, setEnabled] = useState(false)
  const { toast } = useToast()

  const fetchStatus = async () => {
    try {
      const response = await adminFetch('/api/scheduler/status')
      if (!response.ok) throw new Error("Failed to fetch scheduler status")
      const data = await response.json()
      setStatus(data)
      setIntervalValue([data.interval_minutes ?? data.interval])
      setEnabled(data.enabled)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load scheduler status",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const updateScheduler = async () => {
    setSaving(true)
    try {
      const response = await adminFetch('/api/scheduler/config', {
        method: "PUT",
        body: JSON.stringify({
          enabled: enabled,
          interval_minutes: intervalValue[0],
          interval: intervalValue[0],
        }),
      })

      if (!response.ok) throw new Error("Failed to update scheduler")

      toast({
        title: "Success",
        description: "Scheduler configuration updated",
      })
      fetchStatus()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update scheduler configuration",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }


  const formatNextRunTime = (time: string | null) => {
    if (!time) return "Not scheduled"
    const nextRun = new Date(time)
    const now = new Date()
    const diffMs = nextRun.getTime() - now.getTime()
    const diffMins = Math.round(diffMs / 60000)
    
    if (diffMins < 0) return "Overdue"
    if (diffMins === 0) return "Now"
    if (diffMins < 60) return `In ${diffMins} minutes`
    
    const diffHours = Math.round(diffMins / 60)
    return `In ${diffHours} hour${diffHours > 1 ? 's' : ''}`
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading...</div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Sync Scheduler</h1>
        <p className="text-gray-600">Configure automated JIRA synchronization</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Scheduler Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status</span>
              <Badge variant={status?.is_running ? "default" : "secondary"}>
                {status?.is_running ? "Running" : "Stopped"}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Next Sync</span>
              <span className="text-sm text-gray-600">
                {formatNextRunTime(status?.next_run_time || null)}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Configuration
            </CardTitle>
            <CardDescription>
              Configure automated sync settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <Label htmlFor="scheduler-enabled" className="cursor-pointer">
                Enable Scheduler
              </Label>
              <Switch
                id="scheduler-enabled"
                checked={enabled}
                onCheckedChange={setEnabled}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Sync Interval</Label>
                <span className="text-sm text-gray-600">
                  {intervalValue[0]} minutes
                </span>
              </div>
              <Slider
                value={intervalValue}
                onValueChange={setIntervalValue}
                min={2}
                max={120}
                step={1}
                disabled={!enabled}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>2 min</span>
                <span>120 min</span>
              </div>
            </div>

            <Button 
              onClick={updateScheduler} 
              disabled={saving}
              className="w-full"
            >
              {saving ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Configuration"
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Scheduling Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p>• When enabled, syncs will run automatically at the specified interval</p>
            <p>• Syncs will not overlap - if a sync is still running, the next scheduled sync will be skipped</p>
            <p>• Manual syncs can be triggered from the main Dashboard using the "Start Sync" button</p>
            <p>• The scheduler runs independently of manual sync operations</p>
            <p>• Recommended interval: 30-60 minutes for most use cases</p>
          </div>
        </CardContent>
      </Card>
    </div>
    </DashboardLayout>
  )
}