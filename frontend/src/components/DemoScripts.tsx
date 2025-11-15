import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Users, Zap, Skull, Loader2, X } from 'lucide-react'
import { useLanguage } from '../contexts/LanguageContext'

interface DemoScriptsProps {
  onClose: () => void
}

const DEMO_SCRIPTS = [
  {
    id: 'family_drama',
    title: { en: 'Family Drama', ru: 'Семейная драма' },
    description: { en: 'A heartwarming family story', ru: 'Трогательная семейная история' },
    expectedRating: '6+',
    icon: Users,
    color: 'from-blue-500 to-cyan-500',
    file: '/demo/family_drama.txt'
  },
  {
    id: 'action_movie',
    title: { en: 'Action Movie', ru: 'Боевик' },
    description: { en: 'High-octane action thriller', ru: 'Динамичный боевик' },
    expectedRating: '16+',
    icon: Zap,
    color: 'from-orange-500 to-red-500',
    file: '/demo/action_movie.txt'
  },
  {
    id: 'thriller_18',
    title: { en: 'Dark Thriller', ru: 'Темный триллер' },
    description: { en: 'Mature psychological thriller', ru: 'Взрослый психологический триллер' },
    expectedRating: '18+',
    icon: Skull,
    color: 'from-purple-500 to-pink-500',
    file: '/demo/thriller_18.txt'
  }
]

export default function DemoScripts({ onClose }: DemoScriptsProps) {
  const { language } = useLanguage()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [loading, setLoading] = useState<string | null>(null)

  const loadDemoMutation = useMutation({
    mutationFn: async (demo: typeof DEMO_SCRIPTS[0]) => {
      setLoading(demo.id)

      const response = await fetch(demo.file)
      if (!response.ok) throw new Error('Failed to load demo script')
      const content = await response.text()

      const createResponse = await fetch('/api/v1/scripts/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `[DEMO] ${demo.title[language]}`,
          content: content
        })
      })

      if (!createResponse.ok) throw new Error('Failed to create script')
      const script = await createResponse.json()

      const rateResponse = await fetch(`/api/v1/scripts/${script.id}/rate?background=false`, {
        method: 'POST'
      })

      if (!rateResponse.ok) throw new Error('Failed to rate script')

      return script
    },
    onSuccess: (script) => {
      queryClient.invalidateQueries({ queryKey: ['scripts'] })
      navigate(`/scripts/${script.id}`)
      onClose()
    },
    onSettled: () => {
      setLoading(null)
    }
  })

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-4xl w-full border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/40 rounded-lg">
                <Sparkles className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {language === 'ru' ? 'Демо Сценарии' : 'Demo Scripts'}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                  {language === 'ru' ? 'Готовые примеры для демонстрации' : 'Ready examples for demonstration'}
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

        <div className="p-6">
          <div className="grid md:grid-cols-3 gap-4">
            {DEMO_SCRIPTS.map((demo) => {
              const Icon = demo.icon
              const isLoading = loading === demo.id

              return (
                <button
                  key={demo.id}
                  onClick={() => loadDemoMutation.mutate(demo)}
                  disabled={isLoading || !!loading}
                  className="group relative overflow-hidden rounded-xl bg-gradient-to-br p-6 text-left transition-all hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{
                    backgroundImage: `linear-gradient(to bottom right, var(--tw-gradient-stops))`,
                  }}
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${demo.color} opacity-90`}></div>

                  <div className="relative z-10">
                    <div className="flex items-start justify-between mb-4">
                      <div className="p-3 bg-white/20 backdrop-blur-sm rounded-lg">
                        {isLoading ? (
                          <Loader2 className="h-8 w-8 text-white animate-spin" />
                        ) : (
                          <Icon className="h-8 w-8 text-white" />
                        )}
                      </div>
                      <span className="px-3 py-1 bg-white/30 backdrop-blur-sm text-white text-sm font-bold rounded-full">
                        {demo.expectedRating}
                      </span>
                    </div>

                    <h3 className="text-xl font-bold text-white mb-2">
                      {demo.title[language]}
                    </h3>

                    <p className="text-white/90 text-sm mb-4">
                      {demo.description[language]}
                    </p>

                    <div className="flex items-center gap-2 text-white/80 text-xs">
                      <Sparkles className="h-3 w-3" />
                      {isLoading
                        ? (language === 'ru' ? 'Загрузка...' : 'Loading...')
                        : (language === 'ru' ? 'Нажмите для загрузки' : 'Click to load')
                      }
                    </div>
                  </div>
                </button>
              )
            })}
          </div>

          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              <strong>{language === 'ru' ? 'Совет:' : 'Tip:'}</strong>{' '}
              {language === 'ru'
                ? 'Демо сценарии автоматически анализируются после загрузки. Используйте их для демонстрации возможностей системы.'
                : 'Demo scripts are automatically analyzed after loading. Use them to demonstrate system capabilities.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
