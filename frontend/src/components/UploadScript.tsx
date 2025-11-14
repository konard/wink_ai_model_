import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { scriptsApi } from '../api/client'
import { Upload, FileText } from 'lucide-react'

export default function UploadScript() {
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: (data: { file: File; title: string }) =>
      scriptsApi.upload(data.file, data.title),
    onSuccess: (script) => {
      queryClient.invalidateQueries({ queryKey: ['scripts'] })
      navigate(`/scripts/${script.id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (file) {
      uploadMutation.mutate({ file, title: title || file.name })
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-0">
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-5 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">Upload Script</h1>
          <p className="mt-1 text-sm text-gray-500">
            Upload a movie script file to analyze and rate
          </p>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
              Title
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
              placeholder="Enter script title (optional)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Script File
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors">
              <div className="space-y-1 text-center">
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label
                    htmlFor="file-upload"
                    className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none"
                  >
                    <span>Upload a file</span>
                    <input
                      id="file-upload"
                      type="file"
                      className="sr-only"
                      accept=".txt"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">TXT files only</p>
                {file && (
                  <p className="text-sm text-gray-900 font-medium mt-2">
                    Selected: {file.name}
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!file || uploadMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Upload className="h-4 w-4 mr-2" />
              {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
            </button>
          </div>

          {uploadMutation.isError && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">
                Error uploading file. Please try again.
              </p>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
