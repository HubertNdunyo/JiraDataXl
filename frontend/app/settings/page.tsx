'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, ArrowRight, Info } from 'lucide-react'
import DashboardLayout from '../dashboard-layout'

export default function SettingsPage() {
  const router = useRouter()

  return (
    <DashboardLayout>
      <div className="max-w-4xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-gray-600">System configuration and preferences</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Sync Configuration
            </CardTitle>
            <CardDescription>Configure automatic synchronization settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-blue-900">
                  Sync configuration has been moved to the Admin Panel for better control and monitoring.
                </p>
                <p className="text-sm text-blue-700 mt-1">
                  The new scheduler provides advanced features including real-time status, next run time display, and immediate sync triggers.
                </p>
              </div>
            </div>
            
            <Button 
              onClick={() => router.push('/admin/scheduler')}
              className="w-full sm:w-auto"
            >
              Go to Scheduler Settings
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Other Settings</CardTitle>
            <CardDescription>Additional configuration options</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Other system settings will be available here in future updates.
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}