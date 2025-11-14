import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { scriptsApi } from '../api/client'
import { Film, Clock } from 'lucide-react'

export default function ScriptList() {
  const { data: scripts, isLoading } = useQuery({
    queryKey: ['scripts'],
    queryFn: scriptsApi.list,
  })

  if (isLoading) {
    return <div className="text-center py-12">Loading...</div>
  }

  return (
    <div className="px-4 sm:px-0">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Scripts</h1>
          <p className="mt-2 text-sm text-gray-700">
            All uploaded movie scripts and their ratings
          </p>
        </div>
      </div>

      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {scripts?.map((script) => (
          <Link
            key={script.id}
            to={`/scripts/${script.id}`}
            className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center">
                <Film className="h-5 w-5 text-gray-400 mr-2" />
                <h3 className="text-lg font-medium text-gray-900 truncate">
                  {script.title}
                </h3>
              </div>
              {script.predicted_rating && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {script.predicted_rating}
                </span>
              )}
            </div>

            <div className="mt-4 flex items-center text-sm text-gray-500">
              <Clock className="h-4 w-4 mr-1" />
              {new Date(script.created_at).toLocaleDateString()}
            </div>

            {script.total_scenes && (
              <div className="mt-2 text-sm text-gray-500">
                {script.total_scenes} scenes
              </div>
            )}

            {!script.predicted_rating && (
              <div className="mt-3 text-sm text-amber-600">
                Not rated yet
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}
