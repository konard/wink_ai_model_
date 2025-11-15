import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { scriptsApi } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { AlertCircle, Play, FileText, TrendingUp, Lightbulb, Quote, Sparkles, Loader2, Target, Download, FileSpreadsheet, FileCode2, History } from 'lucide-react'
import WhatIfModal from './WhatIfModal'
import RatingAdvisor from './RatingAdvisor'
import SceneHeatmap from './SceneHeatmap'
import VersionHistory from './VersionHistory'
import { useLanguage } from '../contexts/LanguageContext'

const RATING_COLORS: Record<string, string> = {
  '0+': 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 border-green-200 dark:border-green-700',
  '6+': 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400 border-blue-200 dark:border-blue-700',
  '12+': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400 border-yellow-200 dark:border-yellow-700',
  '16+': 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-400 border-orange-200 dark:border-orange-700',
  '18+': 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-400 border-red-200 dark:border-red-700',
}

const CATEGORY_COLORS: Record<string, string> = {
  'violence': '#ef4444',
  'gore': '#dc2626',
  'sex_act': '#f97316',
  'nudity': '#f59e0b',
  'profanity': '#eab308',
  'drugs': '#84cc16',
  'child_risk': '#991b1b',
}

export default function ScriptDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [showWhatIfModal, setShowWhatIfModal] = useState(false)
  const [showRatingAdvisor, setShowRatingAdvisor] = useState(false)
  const [showVersionHistory, setShowVersionHistory] = useState(false)
  const { language, t } = useLanguage()

  const { data: script, isLoading, error } = useQuery({
    queryKey: ['script', id],
    queryFn: () => scriptsApi.get(Number(id)),
  })

  const rateMutation = useMutation({
    mutationFn: () => scriptsApi.rate(Number(id), false),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['script', id] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600 dark:text-blue-400" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 dark:text-red-400 mx-auto mb-4" />
        <div className="text-red-600 dark:text-red-400 mb-2 font-semibold">{t('script.failed_load')}</div>
        <div className="text-gray-600 dark:text-gray-400 text-sm">{(error as Error).message}</div>
      </div>
    )
  }

  if (!script) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
        <div className="text-gray-600 dark:text-gray-400">{t('script.not_found')}</div>
      </div>
    )
  }

  const chartData = script.agg_scores
    ? Object.entries(script.agg_scores).map(([key, value]) => ({
        category: t(`category.${key}`) || key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        score: Number((value * 100).toFixed(1)),
        color: CATEGORY_COLORS[key] || '#3b82f6',
      }))
    : []

  const ratingColor = RATING_COLORS[script.predicted_rating || '6+'] || RATING_COLORS['6+']

  return (
    <div className="px-4 sm:px-0 space-y-6">
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-xl overflow-hidden border border-gray-100 dark:border-gray-700">
        <div className="px-6 py-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">{script.title}</h1>
              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                <span className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  {script.total_scenes || 0} {t('script.scenes')}
                </span>
                <span>{t('script.uploaded')} {new Date(script.created_at).toLocaleString(language === 'ru' ? 'ru-RU' : 'en-US')}</span>
              </div>
            </div>
            {script.predicted_rating ? (
              <div className="flex flex-col items-end gap-3">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowRatingAdvisor(true)}
                    className="inline-flex items-center px-4 py-2 border border-indigo-300 dark:border-indigo-600 rounded-lg text-sm font-medium text-indigo-700 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-indigo-600 transition-all"
                  >
                    <Target className="h-4 w-4 mr-2" />
                    {language === 'ru' ? 'AI Советник' : 'AI Advisor'}
                  </button>
                  <button
                    onClick={() => setShowVersionHistory(true)}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:focus:ring-gray-600 transition-all"
                  >
                    <History className="h-4 w-4 mr-2" />
                    {language === 'ru' ? 'Версии' : 'Versions'}
                  </button>
                  <button
                    onClick={() => setShowWhatIfModal(true)}
                    className="inline-flex items-center px-4 py-2 border border-purple-300 dark:border-purple-600 rounded-lg text-sm font-medium text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/30 hover:bg-purple-100 dark:hover:bg-purple-900/50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 dark:focus:ring-purple-600 transition-all"
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    {t('whatif.title')}
                  </button>
                  <span className={`inline-flex items-center px-6 py-3 rounded-xl text-2xl font-bold border-2 ${ratingColor} shadow-sm`}>
                    {script.predicted_rating}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <a
                    href={`/api/v1/scripts/${id}/export/pdf`}
                    download
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Download className="h-3 w-3 mr-1.5" />
                    PDF
                  </a>
                  <a
                    href={`/api/v1/scripts/${id}/export/excel`}
                    download
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <FileSpreadsheet className="h-3 w-3 mr-1.5" />
                    Excel
                  </a>
                  <a
                    href={`/api/v1/scripts/${id}/export/csv`}
                    download
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <FileCode2 className="h-3 w-3 mr-1.5" />
                    CSV
                  </a>
                </div>
                {script.reasons && script.reasons.length > 0 && (
                  <div className="text-right text-sm text-gray-600 dark:text-gray-400 max-w-xs">
                    {script.reasons.join(', ')}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-end gap-2">
                <button
                  onClick={() => rateMutation.mutate()}
                  disabled={rateMutation.isPending}
                  className="inline-flex items-center px-6 py-3 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-800 focus:ring-blue-500 disabled:opacity-50 transition-all"
                >
                  {rateMutation.isPending ? <Loader2 className="h-5 w-5 mr-2 animate-spin" /> : <Play className="h-5 w-5 mr-2" />}
                  {rateMutation.isPending ? t('script.analyzing') : t('script.analyze')}
                </button>
                {rateMutation.error && (
                  <p className="text-sm text-red-600 dark:text-red-400">{(rateMutation.error as Error).message}</p>
                )}
              </div>
            )}
          </div>
        </div>

        {script.predicted_rating && (
          <>
            {script.evidence_excerpts && script.evidence_excerpts.length > 0 && (
              <div className="px-6 py-6 border-b border-gray-200 dark:border-gray-700 bg-amber-50 dark:bg-amber-900/10">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <Quote className="h-5 w-5 mr-2 text-amber-600 dark:text-amber-500" />
                  {t('script.evidence')}
                </h2>
                <div className="space-y-2">
                  {script.evidence_excerpts.slice(0, 5).map((excerpt, idx) => (
                    <div key={idx} className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-amber-200 dark:border-amber-700 shadow-sm">
                      <p className="text-sm text-gray-700 dark:text-gray-300 italic">"{excerpt}"</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="px-6 py-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <TrendingUp className="h-5 w-5 mr-2 text-blue-600 dark:text-blue-400" />
                {t('script.analysis_scores')}
              </h2>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                  <XAxis
                    dataKey="category"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    className="fill-gray-600 dark:fill-gray-400"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    label={{ value: t('scene.score_label'), angle: -90, position: 'insideLeft', className: 'fill-gray-600 dark:fill-gray-400' }}
                    className="fill-gray-600 dark:fill-gray-400"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--tooltip-bg, #fff)',
                      border: '1px solid var(--tooltip-border, #e5e7eb)',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                    wrapperClassName="dark:[--tooltip-bg:#1f2937] dark:[--tooltip-border:#374151]"
                  />
                  <Legend />
                  <Bar dataKey="score" radius={[8, 8, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {script.scenes && script.scenes.length > 0 && (
              <div className="px-6 py-6">
                <SceneHeatmap scenes={script.scenes} />
              </div>
            )}

            {script.scenes && script.scenes.length > 0 && (
              <div className="px-6 py-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2 text-red-500 dark:text-red-400" />
                  {t('script.high_impact_scenes')}
                </h2>
                <div className="space-y-4">
                  {script.scenes.map((scene, idx) => (
                    <div key={scene.id} className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-850 rounded-xl p-5 border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md dark:shadow-gray-900/50 transition-shadow">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-sm font-bold">
                            {idx + 1}
                          </span>
                          <h3 className="font-semibold text-gray-900 dark:text-white">{scene.heading}</h3>
                        </div>
                        <span className="px-3 py-1 text-sm font-semibold text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/30 rounded-full">
                          {t('script.impact')}: {scene.weight}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                        <div className="bg-white dark:bg-gray-900/50 rounded-lg p-2 text-center border border-gray-200 dark:border-gray-700">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('category.violence')}</div>
                          <div className="text-sm font-bold text-gray-900 dark:text-white">{(scene.violence * 100).toFixed(0)}%</div>
                        </div>
                        <div className="bg-white dark:bg-gray-900/50 rounded-lg p-2 text-center border border-gray-200 dark:border-gray-700">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('category.gore')}</div>
                          <div className="text-sm font-bold text-gray-900 dark:text-white">{(scene.gore * 100).toFixed(0)}%</div>
                        </div>
                        <div className="bg-white dark:bg-gray-900/50 rounded-lg p-2 text-center border border-gray-200 dark:border-gray-700">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('category.sexual')}</div>
                          <div className="text-sm font-bold text-gray-900 dark:text-white">{(scene.sex_act * 100).toFixed(0)}%</div>
                        </div>
                        <div className="bg-white dark:bg-gray-900/50 rounded-lg p-2 text-center border border-gray-200 dark:border-gray-700">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{t('category.profanity')}</div>
                          <div className="text-sm font-bold text-gray-900 dark:text-white">{(scene.profanity * 100).toFixed(0)}%</div>
                        </div>
                      </div>

                      {scene.sample_text && (
                        <div className="bg-white dark:bg-gray-900/50 rounded-lg p-3 mb-3 border border-gray-200 dark:border-gray-700">
                          <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
                            {scene.sample_text}
                          </p>
                        </div>
                      )}

                      {scene.recommendations && scene.recommendations.length > 0 && (
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
                          <div className="flex items-start gap-2">
                            <Lightbulb className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                              <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">{t('scene.recommendations')}</h4>
                              <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-300">
                                {scene.recommendations.map((rec, recIdx) => (
                                  <li key={recIdx} className="flex items-start">
                                    <span className="mr-2">•</span>
                                    <span>{rec}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {showWhatIfModal && script.predicted_rating && (
        <WhatIfModal
          scriptId={Number(id)}
          scriptText={script.content}
          currentRating={script.predicted_rating}
          onClose={() => setShowWhatIfModal(false)}
        />
      )}

      {showRatingAdvisor && script.predicted_rating && (
        <RatingAdvisor
          scriptText={script.content}
          currentRating={script.predicted_rating}
          onClose={() => setShowRatingAdvisor(false)}
        />
      )}

      {showVersionHistory && (
        <VersionHistory
          scriptId={Number(id)}
          onClose={() => setShowVersionHistory(false)}
        />
      )}
    </div>
  )
}
