'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/hooks/use-toast'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Download, Upload, RefreshCw, Clock, Archive, AlertCircle, Plus } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import DashboardLayout from '../../dashboard-layout'

interface Backup {
  id: number
  backup_name: string
  backup_type: string
  created_at: string
  created_by: string
  description?: string
  size?: number
}

export default function BackupsPage() {
  const [backups, setBackups] = useState<Backup[]>([])
  const [loading, setLoading] = useState(true)
  const [restoring, setRestoring] = useState<number | null>(null)
  const [createDialog, setCreateDialog] = useState(false)
  const [restoreDialog, setRestoreDialog] = useState<{ open: boolean; backup?: Backup }>({ open: false })
  const [newBackup, setNewBackup] = useState({ name: '', description: '' })

  const fetchBackups = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/admin/config/backups', {
        headers: {
          'X-Admin-Key': 'jira-admin-key-2024'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setBackups(data.backups || [])
      } else {
        toast({
          title: 'Error',
          description: 'Failed to fetch backups',
          variant: 'destructive'
        })
      }
    } catch (error) {
      console.error('Failed to fetch backups:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch backups',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBackups()
  }, [])

  const createBackup = async () => {
    if (!newBackup.name.trim()) {
      toast({
        title: 'Error',
        description: 'Backup name is required',
        variant: 'destructive'
      })
      return
    }

    try {
      const response = await fetch('/api/admin/config/backups', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Key': 'jira-admin-key-2024'
        },
        body: JSON.stringify({
          name: newBackup.name.trim(),
          description: newBackup.description.trim() || undefined
        })
      })

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Backup created successfully'
        })
        setCreateDialog(false)
        setNewBackup({ name: '', description: '' })
        fetchBackups()
      } else {
        const error = await response.text()
        toast({
          title: 'Error',
          description: error || 'Failed to create backup',
          variant: 'destructive'
        })
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create backup',
        variant: 'destructive'
      })
    }
  }

  const restoreBackup = async (backupId: number) => {
    setRestoring(backupId)
    try {
      const response = await fetch(`/api/admin/config/restore/${backupId}`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': 'jira-admin-key-2024'
        }
      })

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Configuration restored successfully'
        })
        setRestoreDialog({ open: false })
      } else {
        const error = await response.text()
        toast({
          title: 'Error',
          description: error || 'Failed to restore backup',
          variant: 'destructive'
        })
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to restore backup',
        variant: 'destructive'
      })
    } finally {
      setRestoring(null)
    }
  }

  const getBackupTypeBadge = (type: string) => {
    const variants: Record<string, "default" | "secondary" | "outline"> = {
      manual: 'default',
      auto: 'secondary',
      pre_update: 'outline'
    }
    const labels: Record<string, string> = {
      manual: 'Manual',
      auto: 'Automatic',
      pre_update: 'Pre-Update'
    }
    return (
      <Badge variant={variants[type] || 'default'}>
        {labels[type] || type}
      </Badge>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Configuration Backups</h1>
          <p className="text-muted-foreground mt-2">
            Manage and restore configuration backups
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchBackups} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Dialog open={createDialog} onOpenChange={setCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Backup
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Manual Backup</DialogTitle>
                <DialogDescription>
                  Create a new backup of the current configuration
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="backup-name">Backup Name</Label>
                  <Input
                    id="backup-name"
                    placeholder="my-backup-2024"
                    value={newBackup.name}
                    onChange={(e) => setNewBackup({ ...newBackup, name: e.target.value })}
                    pattern="^[a-zA-Z0-9_\-]+$"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Only letters, numbers, dashes and underscores allowed
                  </p>
                </div>
                <div>
                  <Label htmlFor="backup-description">Description (Optional)</Label>
                  <Textarea
                    id="backup-description"
                    placeholder="Description of changes or reason for backup"
                    value={newBackup.description}
                    onChange={(e) => setNewBackup({ ...newBackup, description: e.target.value })}
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setCreateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={createBackup}>
                  Create Backup
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {loading ? (
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center justify-center">
              <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      ) : backups.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <Archive className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Backups Found</h3>
              <p className="text-muted-foreground mb-4">
                No configuration backups have been created yet.
              </p>
              <Button onClick={() => setCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create First Backup
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {backups.map((backup) => (
            <Card key={backup.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <CardTitle className="text-lg flex items-center gap-2">
                      {backup.backup_name}
                      {getBackupTypeBadge(backup.backup_type)}
                    </CardTitle>
                    <CardDescription>
                      {backup.description || 'No description provided'}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <AlertDialog 
                      open={restoreDialog.open && restoreDialog.backup?.id === backup.id}
                      onOpenChange={(open) => setRestoreDialog({ open, backup: open ? backup : undefined })}
                    >
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setRestoreDialog({ open: true, backup })}
                        disabled={restoring !== null}
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Restore
                      </Button>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Restore Configuration?</AlertDialogTitle>
                          <AlertDialogDescription>
                            This will replace the current configuration with the backup "{backup.backup_name}".
                            A new backup of the current configuration will be created automatically before restoring.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => restoreBackup(backup.id)}
                            disabled={restoring === backup.id}
                          >
                            {restoring === backup.id ? (
                              <>
                                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                                Restoring...
                              </>
                            ) : (
                              'Restore'
                            )}
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {formatDistanceToNow(new Date(backup.created_at), { addSuffix: true })}
                  </div>
                  <div>
                    Created by: <span className="font-medium">{backup.created_by}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      </div>
    </DashboardLayout>
  )
}