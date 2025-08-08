'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { 
  AlertTriangle, 
  Save, 
  TestTube, 
  RotateCcw,
  Zap,
  Users,
  Clock,
  Package,
  RefreshCw,
  History,
  Gauge
} from 'lucide-react'
import DashboardLayout from '../../dashboard-layout'

interface PerformanceConfig {
  max_workers: number
  project_timeout: number
  batch_size: number
  lookback_days: number
  max_retries: number
  backoff_factor: number
  rate_limit_pause: number
  connection_pool_size: number
  connection_pool_block: boolean
}

interface TestResult {
  valid: boolean
  warnings: string[]
  estimated_impact: {
    api_requests_per_project: string
    max_concurrent_projects: number
    total_sync_time_estimate: string
    memory_usage: string
    rate_limit_safety: string
  }
}

const DEFAULT_CONFIG: PerformanceConfig = {
  max_workers: 8,
  project_timeout: 300,
  batch_size: 200,
  lookback_days: 60,
  max_retries: 3,
  backoff_factor: 0.5,
  rate_limit_pause: 1.0,
  connection_pool_size: 20,
  connection_pool_block: false
}

export default function PerformanceConfigPage() {
  const [config, setConfig] = useState<PerformanceConfig>(DEFAULT_CONFIG)
  const [originalConfig, setOriginalConfig] = useState<PerformanceConfig>(DEFAULT_CONFIG)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/admin/config/performance', {
        headers: {
          'X-Admin-Key': 'jira-admin-key-2024'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setConfig(data)
        setOriginalConfig(data)
      }
    } catch (error) {
      console.error('Failed to fetch config:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)
    try {
      const response = await fetch('/api/admin/config/performance', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Key': 'jira-admin-key-2024'
        },
        body: JSON.stringify(config)
      })
      
      if (response.ok) {
        const result = await response.json()
        setMessage({ type: 'success', text: result.message })
        setOriginalConfig(config)
        setTestResult(null)
      } else {
        throw new Error('Failed to save configuration')
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save configuration' })
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const response = await fetch('/api/admin/config/performance/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Key': 'jira-admin-key-2024'
        },
        body: JSON.stringify(config)
      })
      
      if (response.ok) {
        const result = await response.json()
        setTestResult(result)
      }
    } catch (error) {
      console.error('Failed to test config:', error)
    } finally {
      setTesting(false)
    }
  }

  const handleReset = () => {
    setConfig(DEFAULT_CONFIG)
    setTestResult(null)
  }

  const handleRevert = () => {
    setConfig(originalConfig)
    setTestResult(null)
  }

  const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig)

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Performance Configuration</h1>
            <p className="text-muted-foreground mt-2">
              Configure sync operation performance parameters
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleRevert}
              disabled={!hasChanges}
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Revert
            </Button>
            <Button
              variant="outline"
              onClick={handleReset}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Reset to Defaults
            </Button>
          </div>
        </div>

        {message && (
          <Alert className={message.type === 'error' ? 'border-red-500' : 'border-green-500'}>
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          {/* Concurrency Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Concurrency Settings
              </CardTitle>
              <CardDescription>
                Control parallel processing and resource usage
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Max Workers</Label>
                  <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                    {config.max_workers}
                  </span>
                </div>
                <Slider
                  value={[config.max_workers]}
                  onValueChange={([value]) => setConfig({ ...config, max_workers: value })}
                  min={1}
                  max={16}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">
                  Number of projects processed simultaneously
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Project Timeout (seconds)</Label>
                  <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                    {config.project_timeout}s
                  </span>
                </div>
                <Slider
                  value={[config.project_timeout]}
                  onValueChange={([value]) => setConfig({ ...config, project_timeout: value })}
                  min={60}
                  max={1800}
                  step={60}
                />
                <p className="text-xs text-muted-foreground">
                  Maximum time to wait for a single project sync
                </p>
              </div>
            </CardContent>
          </Card>

          {/* API Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                API Settings
              </CardTitle>
              <CardDescription>
                Configure API request behavior
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Batch Size</Label>
                  <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                    {config.batch_size}
                  </span>
                </div>
                <Slider
                  value={[config.batch_size]}
                  onValueChange={([value]) => setConfig({ ...config, batch_size: value })}
                  min={50}
                  max={1000}
                  step={50}
                />
                <p className="text-xs text-muted-foreground">
                  Issues fetched per API request
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Rate Limit Pause (seconds)</Label>
                  <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                    {config.rate_limit_pause}s
                  </span>
                </div>
                <Slider
                  value={[config.rate_limit_pause]}
                  onValueChange={([value]) => setConfig({ ...config, rate_limit_pause: value })}
                  min={0}
                  max={10}
                  step={0.5}
                />
                <p className="text-xs text-muted-foreground">
                  Delay between API requests to avoid rate limiting
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Connection Pool Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5" />
                Connection Pool Settings
              </CardTitle>
              <CardDescription>
                Configure HTTP connection pooling for JIRA API
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Connection Pool Size</Label>
                  <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                    {config.connection_pool_size}
                  </span>
                </div>
                <Slider
                  value={[config.connection_pool_size]}
                  onValueChange={([value]) => setConfig({ ...config, connection_pool_size: value })}
                  min={5}
                  max={50}
                  step={5}
                />
                <p className="text-xs text-muted-foreground">
                  Maximum connections to maintain in the pool
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Block on Pool Exhaustion</Label>
                  <Button
                    variant={config.connection_pool_block ? "default" : "outline"}
                    size="sm"
                    onClick={() => setConfig({ ...config, connection_pool_block: !config.connection_pool_block })}
                  >
                    {config.connection_pool_block ? "Enabled" : "Disabled"}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  {config.connection_pool_block ? 
                    "Requests will wait for an available connection" : 
                    "New connections will be created when pool is full"}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Data Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5" />
                Data Settings
              </CardTitle>
              <CardDescription>
                Control data fetching behavior
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Lookback Days</Label>
                  <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                    {config.lookback_days}
                  </span>
                </div>
                <Slider
                  value={[config.lookback_days]}
                  onValueChange={([value]) => setConfig({ ...config, lookback_days: value })}
                  min={1}
                  max={365}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">
                  How many days of issue history to sync
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Retry Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <RefreshCw className="w-5 h-5" />
                Retry Settings
              </CardTitle>
              <CardDescription>
                Configure error handling and retries
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Max Retries</Label>
                  <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                    {config.max_retries}
                  </span>
                </div>
                <Slider
                  value={[config.max_retries]}
                  onValueChange={([value]) => setConfig({ ...config, max_retries: value })}
                  min={0}
                  max={10}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">
                  Number of retry attempts for failed requests
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Backoff Factor</Label>
                  <span className="text-sm font-mono bg-muted px-2 py-1 rounded">
                    {config.backoff_factor}
                  </span>
                </div>
                <Slider
                  value={[config.backoff_factor]}
                  onValueChange={([value]) => setConfig({ ...config, backoff_factor: value })}
                  min={0.1}
                  max={5}
                  step={0.1}
                />
                <p className="text-xs text-muted-foreground">
                  Exponential backoff multiplier between retries
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Test Results */}
        {testResult && (
          <Card className={testResult.warnings.length > 0 ? 'border-yellow-500' : 'border-green-500'}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Gauge className="w-5 h-5" />
                Configuration Test Results
              </CardTitle>
            </CardHeader>
            <CardContent>
              {testResult.warnings.length > 0 && (
                <div className="space-y-2 mb-4">
                  {testResult.warnings.map((warning, idx) => (
                    <Alert key={idx} className="border-yellow-500">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>{warning}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(testResult.estimated_impact).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    <p className="text-lg font-semibold">{value}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={handleTest}
            disabled={testing || !hasChanges}
          >
            <TestTube className="w-4 h-4 mr-2" />
            {testing ? 'Testing...' : 'Test Configuration'}
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !hasChanges}
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </div>
      </div>
    </DashboardLayout>
  )
}