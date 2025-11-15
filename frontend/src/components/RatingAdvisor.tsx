import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { X, Target, TrendingDown, Lightbulb, AlertCircle, CheckCircle2, Loader2, ArrowRight, Zap, Info } from 'lucide-react'
import { useLanguage } from '../contexts/LanguageContext'

const RATING_OPTIONS = ['0+', '6+', '12+', '16+', '18+']

const RATING_COLORS: Record<string, string> = {
  '0+': 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 border-green-200 dark:border-green-700',
  '6+': 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400 border-blue-200 dark:border-blue-700',
  '12+': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400 border-yellow-200 dark:border-yellow-700',
  '16+': 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-400 border-orange-200 dark:border-orange-700',
  '18+': 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 border-red-200 dark:border-red-700',
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20',
  high: 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20',
  medium: 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20',
  low: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20',
}

const SEVERITY_ICONS: Record<string, any> = {
  critical: AlertCircle,
  high: AlertCircle,
  medium: Info,
  low: Info,
}

const DIFFICULTY_BADGES: Record<string, string> = {
  easy: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  medium: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
  hard: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
}

const EFFORT_LABELS = {
  minimal: { en: 'Minimal Effort', ru: 'Минимальные изменения' },
  moderate: { en: 'Moderate Effort', ru: 'Умеренные изменения' },
  significant: { en: 'Significant Effort', ru: 'Значительные изменения' },
  extensive: { en: 'Extensive Effort', ru: 'Масштабные изменения' },
}

interface RatingAdvisorProps {
  scriptText: string
  currentRating: string
  onClose: () => void
}

export default function RatingAdvisor({ scriptText, currentRating, onClose }: RatingAdvisorProps) {
  const { language, t } = useLanguage()
  const [targetRating, setTargetRating] = useState<string>('')
  const [result, setResult] = useState<any>(null)

  const analyzeRating = useMutation({
    mutationFn: async (target: string) => {
      const ML_SERVICE_URL = import.meta.env.VITE_ML_SERVICE_URL || 'http://localhost:8001'
      const response = await fetch(`${ML_SERVICE_URL}/rating_advisor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_text: scriptText,
          current_rating: currentRating,
          target_rating: target,
          language: language,
          include_rewrites: false,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to analyze rating')
      }

      return response.json()
    },
    onSuccess: (data) => {
      setResult(data)
    },
  })

  const handleAnalyze = () => {
    if (targetRating) {
      analyzeRating.mutate(targetRating)
    }
  }

  const availableRatings = RATING_OPTIONS.filter(r => {
    const currentIdx = RATING_OPTIONS.indexOf(currentRating)
    const rIdx = RATING_OPTIONS.indexOf(r)
    return rIdx < currentIdx
  })

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 dark:bg-indigo-900/40 rounded-lg">
                <Target className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {language === 'ru' ? 'AI Советник по Рейтингу' : 'AI Rating Advisor'}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                  {language === 'ru' ? 'Получите рекомендации по изменению рейтинга' : 'Get recommendations to change your rating'}
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

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-88px)]">
          {!result ? (
            <div className="space-y-6">
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-6 border border-blue-100 dark:border-blue-800">
                <div className="flex items-start gap-4">
                  <div className={`px-4 py-2 rounded-lg font-bold text-lg border-2 ${RATING_COLORS[currentRating]}`}>
                    {currentRating}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                      {language === 'ru' ? 'Текущий рейтинг' : 'Current Rating'}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {language === 'ru'
                        ? 'Выберите желаемый рейтинг, и AI проанализирует что нужно изменить'
                        : 'Select your desired rating and AI will analyze what needs to change'}
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  {language === 'ru' ? 'Выберите целевой рейтинг' : 'Select Target Rating'}
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  {availableRatings.map((rating) => (
                    <button
                      key={rating}
                      onClick={() => setTargetRating(rating)}
                      className={`px-4 py-3 rounded-lg font-bold text-lg border-2 transition-all ${
                        targetRating === rating
                          ? RATING_COLORS[rating] + ' ring-4 ring-offset-2 ring-indigo-200 dark:ring-indigo-800 scale-105'
                          : 'border-gray-200 dark:border-gray-600 text-gray-400 dark:text-gray-500 hover:border-gray-300 dark:hover:border-gray-500'
                      }`}
                    >
                      {rating}
                    </button>
                  ))}
                </div>
                {availableRatings.length === 0 && (
                  <div className="text-center py-6 text-gray-500 dark:text-gray-400">
                    <Info className="h-8 w-8 mx-auto mb-2" />
                    <p>{language === 'ru' ? 'Невозможно понизить рейтинг дальше' : 'Cannot lower rating further'}</p>
                  </div>
                )}
              </div>

              {targetRating && (
                <button
                  onClick={handleAnalyze}
                  disabled={analyzeRating.isPending}
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold py-4 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {analyzeRating.isPending ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      {language === 'ru' ? 'Анализ...' : 'Analyzing...'}
                    </>
                  ) : (
                    <>
                      <Zap className="h-5 w-5" />
                      {language === 'ru' ? 'Получить рекомендации' : 'Get Recommendations'}
                      <ArrowRight className="h-5 w-5" />
                    </>
                  )}
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl p-6 border border-indigo-100 dark:border-indigo-800">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`px-4 py-2 rounded-lg font-bold text-lg border-2 ${RATING_COLORS[result.current_rating]}`}>
                      {result.current_rating}
                    </div>
                    <ArrowRight className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                    <div className={`px-4 py-2 rounded-lg font-bold text-lg border-2 ${RATING_COLORS[result.target_rating]}`}>
                      {result.target_rating}
                    </div>
                  </div>
                  {result.is_achievable ? (
                    <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                      <CheckCircle2 className="h-5 w-5" />
                      <span className="font-semibold">
                        {language === 'ru' ? 'Достижимо' : 'Achievable'}
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                      <AlertCircle className="h-5 w-5" />
                      <span className="font-semibold">
                        {language === 'ru' ? 'Недостижимо' : 'Not Achievable'}
                      </span>
                    </div>
                  )}
                </div>

                <p className="text-gray-700 dark:text-gray-300 mb-3">{result.summary}</p>

                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 dark:text-gray-400">
                      {language === 'ru' ? 'Уверенность:' : 'Confidence:'}
                    </span>
                    <div className="bg-white dark:bg-gray-700 px-3 py-1 rounded-full font-semibold">
                      {(result.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 dark:text-gray-400">
                      {language === 'ru' ? 'Усилия:' : 'Effort:'}
                    </span>
                    <div className="bg-white dark:bg-gray-700 px-3 py-1 rounded-full font-semibold">
                      {EFFORT_LABELS[result.estimated_effort as keyof typeof EFFORT_LABELS]?.[language] || result.estimated_effort}
                    </div>
                  </div>
                </div>
              </div>

              {result.rating_gaps && result.rating_gaps.length > 0 && (
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <TrendingDown className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                    {language === 'ru' ? 'Необходимые изменения' : 'Required Changes'}
                  </h3>
                  <div className="grid gap-3">
                    {result.rating_gaps.map((gap: any, idx: number) => (
                      <div key={idx} className={`p-4 rounded-lg border ${PRIORITY_COLORS[gap.priority]}`}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm uppercase tracking-wide">{gap.priority}</span>
                            <span className="text-gray-700 dark:text-gray-300 font-medium">{gap.dimension}</span>
                          </div>
                          <span className="text-sm font-mono bg-white dark:bg-gray-800 px-2 py-1 rounded">
                            -{(gap.gap * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-gray-600 dark:text-gray-400">
                            {gap.current_score.toFixed(2)} → {gap.target_score.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.problematic_scenes && result.problematic_scenes.length > 0 && (
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <AlertCircle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                    {language === 'ru' ? 'Проблемные сцены' : 'Problematic Scenes'}
                  </h3>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {result.problematic_scenes.slice(0, 10).map((scene: any) => {
                      const SeverityIcon = SEVERITY_ICONS[scene.severity]
                      return (
                        <div key={scene.scene_id} className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                          <div className="flex items-start gap-3">
                            <div className="mt-1">
                              <SeverityIcon className={`h-5 w-5 ${scene.severity === 'critical' || scene.severity === 'high' ? 'text-red-500' : 'text-yellow-500'}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="font-semibold text-gray-900 dark:text-white">
                                  {language === 'ru' ? 'Сцена' : 'Scene'} {scene.scene_number}
                                </span>
                                <span className={`text-xs px-2 py-0.5 rounded-full uppercase font-semibold ${PRIORITY_COLORS[scene.severity]}`}>
                                  {scene.severity}
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">
                                {scene.content_preview}
                              </p>
                              <div className="flex flex-wrap gap-2 mb-2">
                                {Object.entries(scene.issues).map(([dim, val]: [string, any]) => (
                                  <span key={dim} className="text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 px-2 py-1 rounded">
                                    {dim}: +{(val * 100).toFixed(0)}%
                                  </span>
                                ))}
                              </div>
                              {scene.recommendations && scene.recommendations.length > 0 && (
                                <ul className="text-sm space-y-1">
                                  {scene.recommendations.map((rec: string, ridx: number) => (
                                    <li key={ridx} className="text-gray-700 dark:text-gray-300 flex items-start gap-2">
                                      <span className="text-indigo-500 mt-0.5">•</span>
                                      <span>{rec}</span>
                                    </li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {result.recommended_actions && result.recommended_actions.length > 0 && (
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                    {language === 'ru' ? 'Рекомендованные действия' : 'Recommended Actions'}
                  </h3>
                  <div className="space-y-3">
                    {result.recommended_actions.slice(0, 15).map((action: any, idx: number) => (
                      <div key={idx} className="bg-white dark:bg-gray-900/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
                        <div className="flex items-start gap-3">
                          <div className="mt-1">
                            <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-sm">
                              {idx + 1}
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <span className={`text-xs px-2 py-1 rounded font-semibold ${DIFFICULTY_BADGES[action.difficulty]}`}>
                                {action.difficulty}
                              </span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {language === 'ru' ? 'Влияние:' : 'Impact:'} {(action.impact_score * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-gray-900 dark:text-white font-medium mb-1">
                              {action.description}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                              {action.category}
                            </p>
                            {action.specific_changes && action.specific_changes.length > 0 && (
                              <div className="text-sm text-indigo-600 dark:text-indigo-400">
                                {action.specific_changes.join(', ')}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.alternative_targets && result.alternative_targets.length > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border border-yellow-200 dark:border-yellow-800">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    {language === 'ru' ? 'Альтернативные цели:' : 'Alternative Targets:'}
                  </h4>
                  <div className="flex gap-2">
                    {result.alternative_targets.map((alt: string) => (
                      <button
                        key={alt}
                        onClick={() => {
                          setTargetRating(alt)
                          setResult(null)
                        }}
                        className={`px-3 py-1 rounded-lg font-bold border-2 ${RATING_COLORS[alt]} hover:opacity-80 transition-opacity`}
                      >
                        {alt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => {
                  setResult(null)
                  setTargetRating('')
                }}
                className="w-full bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-semibold py-3 px-6 rounded-xl transition-colors"
              >
                {language === 'ru' ? 'Начать заново' : 'Start Over'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
