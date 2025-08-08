'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { FileJson, Settings, Shield, Info, Zap } from 'lucide-react'
import Link from 'next/link'
import DashboardLayout from '../dashboard-layout'

export default function AdminOverview() {
  return (
    <DashboardLayout>
      <div>
      <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <Link href="/admin/field-mappings">
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileJson className="w-5 h-5" />
                Field Mappings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                View and manage field mappings between JIRA instances
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/admin/sync-config">
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Sync Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Configure sync interval and automatic sync settings
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/admin/performance">
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Performance Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Optimize sync performance and resource usage
              </p>
            </CardContent>
          </Card>
        </Link>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Security
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Protected with admin API key authentication
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="w-5 h-5" />
            MVP Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc list-inside space-y-2 text-sm">
            <li>View current field mappings configuration</li>
            <li>Adjust sync interval (1-1440 minutes)</li>
            <li>JSON viewer with syntax highlighting</li>
            <li>Configuration backup on changes</li>
            <li>Basic API key authentication</li>
          </ul>
        </CardContent>
      </Card>
      </div>
    </DashboardLayout>
  )
}