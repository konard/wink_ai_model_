import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { scriptsApi } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { AlertCircle, Play } from 'lucide-react'

export default function ScriptDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const { data: script, isLoading } = useQuery({
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
    return <div className="text-center py-12">Loading...</div>
  }

  if (!script) {
    return <div className="text-center py-12">Script not found</div>
  }

  const chartData = script.agg_scores
    ? Object.entries(script.agg_scores).map(([key, value]) => ({
        category: key.replace('_', ' '),
        score: Number((value * 100).toFixed(1)),
      }))
    : []

  return (
    <div className="px-4 sm:px-0">
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-5 border-b border-gray-200">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{script.title}</h1>
              <p className="mt-1 text-sm text-gray-500">
                Uploaded {new Date(script.created_at).toLocaleString()}
              </p>
            </div>
            {script.predicted_rating ? (
              <span className="inline-flex items-center px-4 py-2 rounded-full text-lg font-medium bg-blue-100 text-blue-800">
                {script.predicted_rating}
              </span>
            ) : (
              <button
                onClick={() => rateMutation.mutate()}
                disabled={rateMutation.isPending}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <Play className="h-4 w-4 mr-2" />
                {rateMutation.isPending ? 'Rating...' : 'Rate Script'}
              </button>
            )}
          </div>
        </div>

        {script.predicted_rating && (
          <>
            <div className="px-6 py-5">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Content Scores</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="score" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {script.scenes && script.scenes.length > 0 && (
              <div className="px-6 py-5 border-t border-gray-200">
                <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2 text-amber-500" />
                  Top Trigger Scenes
                </h2>
                <div className="space-y-4">
                  {script.scenes.map((scene) => (
                    <div key={scene.id} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-medium text-gray-900">{scene.heading}</h3>
                        <span className="text-sm font-medium text-gray-600">
                          Weight: {scene.weight}
                        </span>
                      </div>
                      <div className="grid grid-cols-4 gap-2 text-sm">
                        <div>Violence: {(scene.violence * 100).toFixed(0)}%</div>
                        <div>Gore: {(scene.gore * 100).toFixed(0)}%</div>
                        <div>Sexual: {(scene.sex_act * 100).toFixed(0)}%</div>
                        <div>Profanity: {(scene.profanity * 100).toFixed(0)}%</div>
                      </div>
                      {scene.sample_text && (
                        <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                          {scene.sample_text}
                        </p>
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
