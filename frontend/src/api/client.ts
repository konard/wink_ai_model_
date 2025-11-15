import axios, { AxiosError } from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      const detail = (error.response.data as { detail?: string })?.detail
      throw new Error(detail || `Server error: ${error.response.status}`)
    } else if (error.request) {
      throw new Error('Network error: Unable to reach the server')
    } else {
      throw new Error('Request failed: ' + error.message)
    }
  }
)

export interface Script {
  id: number
  title: string
  predicted_rating: string | null
  agg_scores: Record<string, number> | null
  model_version: string | null
  total_scenes: number | null
  created_at: string
  updated_at: string | null
  reasons?: string[]
  evidence_excerpts?: string[]
}

export interface Scene {
  id: number
  scene_id: number
  heading: string
  violence: number
  gore: number
  sex_act: number
  nudity: number
  profanity: number
  drugs: number
  child_risk: number
  weight: number
  sample_text: string | null
  recommendations?: string[]
}

export interface ScriptDetail extends Script {
  scenes: Scene[]
}

export interface RatingJob {
  job_id: string
  script_id: number
  status: string
  message: string
}

export const scriptsApi = {
  list: async (): Promise<Script[]> => {
    const { data } = await apiClient.get('/scripts/')
    return data
  },

  get: async (id: number): Promise<ScriptDetail> => {
    const { data } = await apiClient.get(`/scripts/${id}`)
    return data
  },

  create: async (title: string, content: string): Promise<Script> => {
    const { data } = await apiClient.post('/scripts/', { title, content })
    return data
  },

  upload: async (file: File, title?: string): Promise<Script> => {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)

    const { data } = await apiClient.post('/scripts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  rate: async (id: number, background = true): Promise<RatingJob> => {
    const { data } = await apiClient.post(`/scripts/${id}/rate?background=${background}`)
    return data
  },

  jobStatus: async (jobId: string) => {
    const { data } = await apiClient.get(`/scripts/jobs/${jobId}/status`)
    return data
  },
}

export default apiClient
