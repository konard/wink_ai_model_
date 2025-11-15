import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { History, GitBranch, RotateCcw, Trash2, Eye, X, Clock, FileText } from 'lucide-react'
import { useLanguage } from '../contexts/LanguageContext'

interface Version {
  id: number
  version_number: number
  title: string
  predicted_rating: string | null
  total_scenes: number
  change_description: string | null
  is_current: boolean
  created_at: string
}

interface VersionHistoryProps {
  scriptId: number
  onClose: () => void
}

export default function VersionHistory({ scriptId, onClose }: VersionHistoryProps) {
  const { language } = useLanguage()
  const queryClient = useQueryClient()
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null)

  const { data: versions, isLoading } = useQuery<Version[]>({
    queryKey: ['versions', scriptId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/scripts/${scriptId}/versions`)
      if (!response.ok) throw new Error('Failed to load versions')
      return response.json()
    }
  })

  const createVersionMutation = useMutation({
    mutationFn: async (description: string) => {
      const response = await fetch(`/api/v1/scripts/${scriptId}/versions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          change_description: description,
          make_current: true
        })
      })
      if (!response.ok) throw new Error('Failed to create version')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['versions', scriptId] })
      queryClient.invalidateQueries({ queryKey: ['script', scriptId.toString()] })
    }
  })

  const restoreVersionMutation = useMutation({
    mutationFn: async (versionNumber: number) => {
      const response = await fetch(`/api/v1/scripts/${scriptId}/versions/${versionNumber}/restore`, {
        method: 'POST'
      })
      if (!response.ok) throw new Error('Failed to restore version')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['versions', scriptId] })
      queryClient.invalidateQueries({ queryKey: ['script', scriptId.toString()] })
    }
  })

  const deleteVersionMutation = useMutation({
    mutationFn: async (versionNumber: number) => {
      const response = await fetch(`/api/v1/scripts/${scriptId}/versions/${versionNumber}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to delete version')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['versions', scriptId] })
    }
  })

  const handleCreateVersion = () => {
    const description = prompt(
      language === 'ru' ? 'Описание версии:' : 'Version description:',
      language === 'ru' ? 'Сохранение текущего состояния' : 'Save current state'
    )
    if (description) {
      createVersionMutation.mutate(description)
    }
  }

  const handleRestore = (versionNumber: number) => {
    if (window.confirm(
      language === 'ru'
        ? `Восстановить версию ${versionNumber}? Текущее состояние будет сохранено как резервная копия.`
        : `Restore version ${versionNumber}? Current state will be saved as backup.`
    )) {
      restoreVersionMutation.mutate(versionNumber)
    }
  }

  const handleDelete = (versionNumber: number) => {
    if (window.confirm(
      language === 'ru'
        ? `Удалить версию ${versionNumber}? Это действие необратимо.`
        : `Delete version ${versionNumber}? This action cannot be undone.`
    )) {
      deleteVersionMutation.mutate(versionNumber)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/40 rounded-lg">
                <History className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {language === 'ru' ? 'История версий' : 'Version History'}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                  {language === 'ru' ? 'Управление версиями сценария' : 'Manage script versions'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/50 dark:hover:bg-gray-700/50 rounded-lg transition-colors"
            >
              <X className="h-6 w-6 text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="mb-6">
            <button
              onClick={handleCreateVersion}
              disabled={createVersionMutation.isPending}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <GitBranch className="h-5 w-5" />
              {language === 'ru' ? 'Создать новую версию' : 'Create New Version'}
            </button>
          </div>

          {isLoading ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              {language === 'ru' ? 'Загрузка...' : 'Loading...'}
            </div>
          ) : !versions || versions.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              {language === 'ru' ? 'Нет сохраненных версий' : 'No saved versions'}
            </div>
          ) : (
            <div className="space-y-3">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className={`bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 border ${
                    version.is_current
                      ? 'border-blue-500 dark:border-blue-400 ring-2 ring-blue-200 dark:ring-blue-800'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <GitBranch className="h-4 w-4 text-gray-500" />
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {language === 'ru' ? 'Версия' : 'Version'} {version.version_number}
                          </span>
                        </div>
                        {version.is_current && (
                          <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 text-xs font-semibold rounded">
                            {language === 'ru' ? 'Текущая' : 'Current'}
                          </span>
                        )}
                        {version.predicted_rating && (
                          <span className="px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-semibold rounded">
                            {version.predicted_rating}
                          </span>
                        )}
                      </div>

                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(version.created_at).toLocaleString(
                              language === 'ru' ? 'ru-RU' : 'en-US'
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <FileText className="h-3 w-3" />
                            {version.total_scenes} {language === 'ru' ? 'сцен' : 'scenes'}
                          </div>
                        </div>
                      </div>

                      {version.change_description && (
                        <p className="text-sm text-gray-700 dark:text-gray-300 italic">
                          "{version.change_description}"
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      {!version.is_current && (
                        <>
                          <button
                            onClick={() => handleRestore(version.version_number)}
                            disabled={restoreVersionMutation.isPending}
                            className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                            title={language === 'ru' ? 'Восстановить' : 'Restore'}
                          >
                            <RotateCcw className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(version.version_number)}
                            disabled={deleteVersionMutation.isPending}
                            className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                            title={language === 'ru' ? 'Удалить' : 'Delete'}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
