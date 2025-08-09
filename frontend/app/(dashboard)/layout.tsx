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
          
          <nav className="space-y-1">
            {dashboardRoutes.map((route) => (
              <div key={route.path}>
                {route.subItems ? (
                  <>
                    <button
                      onClick={() => setAdminExpanded(!adminExpanded)}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left",
                        pathname?.startsWith(route.path)
                          ? "bg-gray-800 text-white"
                          : "text-gray-300 hover:bg-gray-800 hover:text-white"
                      )}
                    >
                      <route.icon className="w-5 h-5" />
                      <span className="flex-1">{route.label}</span>
                      {adminExpanded ? 
                        <ChevronDown className="w-4 h-4" /> : 
                        <ChevronRight className="w-4 h-4" />
                      }
                    </button>
                    {adminExpanded && (
                      <div className="ml-4 mt-1 space-y-1">
                        {route.subItems.map((subItem) => (
                          <Link
                            key={subItem.path}
                            href={subItem.path}
                            className={cn(
                              "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                              pathname === subItem.path
                                ? "bg-gray-800 text-white"
                                : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
                            )}
                          >
                            <subItem.icon className="w-4 h-4" />
                            <span className="text-sm">{subItem.label}</span>
                          </Link>
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <Link
                    href={route.path}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                      pathname === route.path
                        ? "bg-gray-800 text-white"
                        : "text-gray-300 hover:bg-gray-800 hover:text-white"
                    )}
                  >
                    <route.icon className="w-5 h-5" />
                    <span>{route.label}</span>
                  </Link>
                )}
              </div>
            ))}
          </nav>
        </div>
        
        <div className="mt-auto p-6 border-t border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-400">System Active</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 bg-gray-50 overflow-auto">
        {children}
      </main>
    </div>
  )
}