import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { scriptsApi } from '../api/client'
import { Film, Clock, Loader2, Sparkles } from 'lucide-react'
import { useLanguage } from '../contexts/LanguageContext'
import DemoScripts from './DemoScripts'

export default function ScriptList() {
  const { language, t } = useLanguage()
  const [showDemoScripts, setShowDemoScripts] = useState(false)
  const { data: scripts, isLoading, error } = useQuery({
    queryKey: ['scripts'],
    queryFn: scriptsApi.list,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600 dark:text-blue-400" />
        <span className="ml-3 text-gray-700 dark:text-gray-300">{t('common.loading')}</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 dark:text-red-400 mb-2 font-semibold">{t('script.failed_load')}</div>
        <div className="text-gray-600 dark:text-gray-400 text-sm">{(error as Error).message}</div>
      </div>
    )
  }

  return (
    <div className="px-4 sm:px-0">
      <div className="sm:flex sm:items-center mb-8">
        <div className="sm:flex-auto">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('script.list_title')}</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            {t('script.list_subtitle')}
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            onClick={() => setShowDemoScripts(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg hover:from-purple-700 hover:to-pink-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600 transition-all"
          >
            <Sparkles className="h-4 w-4" />
            {language === 'ru' ? 'Демо Сценарии' : 'Demo Scripts'}
          </button>
        </div>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {scripts?.map((script) => (
          <Link
            key={script.id}
            to={`/scripts/${script.id}`}
            className="group block p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-xl dark:shadow-gray-900/50 transition-all duration-300 border border-gray-100 dark:border-gray-700 hover:scale-[1.02]"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center flex-1 min-w-0">
                <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 dark:from-blue-600 dark:to-indigo-700 rounded-lg mr-3 group-hover:scale-110 transition-transform">
                  <Film className="h-5 w-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                  {script.title}
                </h3>
              </div>
              {script.predicted_rating && (
                <span className="ml-2 inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-sm">
                  {script.predicted_rating}
                </span>
              )}
            </div>

            <div className="flex items-center text-sm text-gray-500 dark:text-gray-400 mb-2">
              <Clock className="h-4 w-4 mr-2" />
              {new Date(script.created_at).toLocaleDateString(language === 'ru' ? 'ru-RU' : 'en-US')}
            </div>

            {script.total_scenes && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {script.total_scenes} {t('script.scenes')}
              </div>
            )}

            {!script.predicted_rating && (
              <div className="mt-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                {t('script.not_rated')}
              </div>
            )}
          </Link>
        ))}
      </div>

      {showDemoScripts && (
        <DemoScripts onClose={() => setShowDemoScripts(false)} />
      )}
    </div>
  )
}
