'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Activity, Settings, Clock, Shield, Home, ChevronDown, ChevronRight, FileJson, Archive, BarChart, Zap, Calendar, TestTube } from 'lucide-react'
import { cn } from '@/lib/utils'

interface RouteItem {
  path: string
  label: string
  icon: any
  subItems?: RouteItem[]
}

const dashboardRoutes: RouteItem[] = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/history', label: 'Sync History', icon: Clock },
  { path: '/settings', label: 'Settings', icon: Settings },
  { 
    path: '/admin', 
    label: 'Admin Panel', 
    icon: Shield,
    subItems: [
      { path: '/admin', label: 'Overview', icon: BarChart },
      { path: '/admin/field-mappings', label: 'Field Mappings', icon: FileJson },
      { path: '/admin/sync-config', label: 'Sync Settings', icon: Settings },
      { path: '/admin/performance', label: 'Performance', icon: Zap },
      { path: '/admin/scheduler', label: 'Scheduler', icon: Calendar },
      { path: '/admin/backups', label: 'Backups', icon: Archive },
      { path: '/admin/inua-test', label: 'INUA Testing', icon: TestTube },
    ]
  },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [adminExpanded, setAdminExpanded] = useState(pathname?.startsWith('/admin') || false)

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white flex flex-col h-full">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <Activity className="w-8 h-8 text-blue-400" />
            <div>
              <h1 className="text-xl font-bold">JIRA Sync</h1>
              <p className="text-xs text-gray-400">Management Dashboard</p>
            </div>
          </div>
          <nav className="space-y-2">
            {dashboardRoutes.map((route) => {
              const Icon = route.icon
              const isActive = route.subItems 
                ? pathname?.startsWith(route.path) 
                : pathname === route.path
              
              if (route.subItems) {
                return (
                  <div key={route.path}>
                    <button
                      onClick={() => setAdminExpanded(!adminExpanded)}
                      className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200",
                        isActive
                          ? "bg-gray-800 text-white"
                          : "text-gray-300 hover:bg-gray-800 hover:text-white"
                      )}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="flex-1 text-left">{route.label}</span>
                      {adminExpanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                    {adminExpanded && (
                      <div className="mt-2 space-y-1">
                        {route.subItems.map((subItem) => {
                          const SubIcon = subItem.icon
                          const isSubActive = pathname === subItem.path ||
                            (subItem.path !== '/admin' && pathname?.startsWith(subItem.path))
                          return (
                            <Link
                              key={subItem.path}
                              href={subItem.path}
                              className={cn(
                                "flex items-center gap-3 px-4 py-2 ml-4 rounded-lg transition-all duration-200 text-sm",
                                isSubActive
                                  ? "bg-gray-700 text-white"
                                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
                              )}
                            >
                              <SubIcon className="w-3 h-3" />
                              {subItem.label}
                            </Link>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              }
              
              return (
                <Link
                  key={route.path}
                  href={route.path}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200",
                    isActive
                      ? "bg-gray-800 text-white"
                      : "text-gray-300 hover:bg-gray-800 hover:text-white"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {route.label}
                </Link>
              )
            })}
          </nav>
        </div>
        
        {/* Bottom section */}
        <div className="mt-auto p-6 border-t border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-sm font-semibold">
              A
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">Admin</p>
              <p className="text-xs text-gray-400">System Administrator</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Page content */}
        <main className="flex-1 bg-gray-50 overflow-auto">
          <div className="p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}