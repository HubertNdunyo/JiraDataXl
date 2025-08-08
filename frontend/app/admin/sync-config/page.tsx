'use client'

import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, ArrowRight, Info, Calendar } from 'lucide-react'
import DashboardLayout from '../../dashboard-layout'

export default function SyncConfigPage() {
  const router = useRouter()

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Sync Settings</h1>
          <p className="text-gray-600">Advanced synchronization configuration</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Automated Sync Scheduler
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-blue-900 font-medium">
                  Sync scheduling has been consolidated
                </p>
                <p className="text-sm text-blue-700 mt-1">
                  All sync scheduling features including interval configuration, enable/disable controls, 
                  and real-time status monitoring are now available in the dedicated Scheduler page.
                </p>
              </div>
            </div>
            
            <Button 
              onClick={() => router.push('/admin/scheduler')}
              className="w-full sm:w-auto"
            >
              Configure Scheduler
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Advanced Sync Settings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              Additional sync configuration options are managed in other admin sections:
            </p>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-gray-400 rounded-full mt-1.5"></div>
                <div>
                  <p className="text-sm font-medium">Performance Settings</p>
                  <p className="text-sm text-gray-600">Batch size, workers, timeouts → <span className="text-blue-600 cursor-pointer" onClick={() => router.push('/admin/performance')}>Performance page</span></p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-gray-400 rounded-full mt-1.5"></div>
                <div>
                  <p className="text-sm font-medium">Field Mappings</p>
                  <p className="text-sm text-gray-600">Configure JIRA field synchronization → <span className="text-blue-600 cursor-pointer" onClick={() => router.push('/admin/field-mappings')}>Field Mappings page</span></p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 bg-gray-400 rounded-full mt-1.5"></div>
                <div>
                  <p className="text-sm font-medium">Error Handling</p>
                  <p className="text-sm text-gray-600">Retry settings, error notifications → Coming soon</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}