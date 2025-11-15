import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { scriptsApi } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { AlertCircle, Play, FileText, TrendingUp, Lightbulb, Quote } from 'lucide-react'

const RATING_COLORS: Record<string, string> = {
  '0+': 'bg-green-100 text-green-800 border-green-200',
  '6+': 'bg-blue-100 text-blue-800 border-blue-200',
  '12+': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  '16+': 'bg-orange-100 text-orange-800 border-orange-200',
  '18+': 'bg-red-100 text-red-800 border-red-200',
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <div className="text-red-600 mb-2 font-medium">Failed to load script</div>
        <div className="text-gray-600 text-sm">{(error as Error).message}</div>
      </div>
    )
  }

  if (!script) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <div className="text-gray-600">Script not found</div>
      </div>
    )
  }

  const chartData = script.agg_scores
    ? Object.entries(script.agg_scores).map(([key, value]) => ({
        category: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        score: Number((value * 100).toFixed(1)),
        color: CATEGORY_COLORS[key] || '#3b82f6',
      }))
    : []

  const ratingColor = RATING_COLORS[script.predicted_rating || '6+'] || RATING_COLORS['6+']

  return (
    <div className="px-4 sm:px-0 space-y-6">
      <div className="bg-white shadow-lg rounded-xl overflow-hidden">
        <div className="px-6 py-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{script.title}</h1>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  {script.total_scenes || 0} scenes
                </span>
                <span>Uploaded {new Date(script.created_at).toLocaleString()}</span>
              </div>
            </div>
            {script.predicted_rating ? (
              <div className="flex flex-col items-end gap-2">
                <span className={`inline-flex items-center px-6 py-3 rounded-xl text-2xl font-bold border-2 ${ratingColor} shadow-sm`}>
                  {script.predicted_rating}
                </span>
                {script.reasons && script.reasons.length > 0 && (
                  <div className="text-right text-sm text-gray-600 max-w-xs">
                    {script.reasons.join(', ')}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-end gap-2">
                <button
                  onClick={() => rateMutation.mutate()}
                  disabled={rateMutation.isPending}
                  className="inline-flex items-center px-6 py-3 border border-transparent rounded-lg shadow-sm text-base font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-all"
                >
                  <Play className="h-5 w-5 mr-2" />
                  {rateMutation.isPending ? 'Analyzing...' : 'Analyze Script'}
                </button>
                {rateMutation.error && (
                  <p className="text-sm text-red-600">{(rateMutation.error as Error).message}</p>
                )}
              </div>
            )}
          </div>
        </div>

        {script.predicted_rating && (
          <>
            {script.evidence_excerpts && script.evidence_excerpts.length > 0 && (
              <div className="px-6 py-6 border-b border-gray-200 bg-amber-50">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Quote className="h-5 w-5 mr-2 text-amber-600" />
                  Evidence from Script
                </h2>
                <div className="space-y-2">
                  {script.evidence_excerpts.slice(0, 5).map((excerpt, idx) => (
                    <div key={idx} className="bg-white rounded-lg p-3 border border-amber-200 shadow-sm">
                      <p className="text-sm text-gray-700 italic">"{excerpt}"</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="px-6 py-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <TrendingUp className="h-5 w-5 mr-2 text-blue-600" />
                Content Analysis Scores
              </h2>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="category"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    tick={{ fill: '#4b5563', fontSize: 12 }}
                  />
                  <YAxis
                    label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }}
                    tick={{ fill: '#4b5563' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
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
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2 text-red-500" />
                  High-Impact Scenes
                </h2>
                <div className="space-y-4">
                  {script.scenes.map((scene, idx) => (
                    <div key={scene.id} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-red-100 text-red-700 text-sm font-bold">
                            {idx + 1}
                          </span>
                          <h3 className="font-semibold text-gray-900">{scene.heading}</h3>
                        </div>
                        <span className="px-3 py-1 text-sm font-semibold text-red-700 bg-red-100 rounded-full">
                          Impact: {scene.weight}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                        <div className="bg-white rounded-lg p-2 text-center border border-gray-200">
                          <div className="text-xs text-gray-500 mb-1">Violence</div>
                          <div className="text-sm font-bold text-gray-900">{(scene.violence * 100).toFixed(0)}%</div>
                        </div>
                        <div className="bg-white rounded-lg p-2 text-center border border-gray-200">
                          <div className="text-xs text-gray-500 mb-1">Gore</div>
                          <div className="text-sm font-bold text-gray-900">{(scene.gore * 100).toFixed(0)}%</div>
                        </div>
                        <div className="bg-white rounded-lg p-2 text-center border border-gray-200">
                          <div className="text-xs text-gray-500 mb-1">Sexual</div>
                          <div className="text-sm font-bold text-gray-900">{(scene.sex_act * 100).toFixed(0)}%</div>
                        </div>
                        <div className="bg-white rounded-lg p-2 text-center border border-gray-200">
                          <div className="text-xs text-gray-500 mb-1">Profanity</div>
                          <div className="text-sm font-bold text-gray-900">{(scene.profanity * 100).toFixed(0)}%</div>
                        </div>
                      </div>

                      {scene.sample_text && (
                        <div className="bg-white rounded-lg p-3 mb-3 border border-gray-200">
                          <p className="text-sm text-gray-700 line-clamp-3">
                            {scene.sample_text}
                          </p>
                        </div>
                      )}

                      {scene.recommendations && scene.recommendations.length > 0 && (
                        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                          <div className="flex items-start gap-2">
                            <Lightbulb className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                            <div className="flex-1">
                              <h4 className="text-sm font-semibold text-blue-900 mb-2">Recommendations</h4>
                              <ul className="space-y-1 text-sm text-blue-800">
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
    </div>
  )
}
