import { useMemo } from 'react'
import { Scene } from '../api/client'

interface SceneHeatmapProps {
  scenes: Scene[]
}

const CATEGORIES = [
  { key: 'violence', label: { en: 'Violence', ru: 'Насилие' } },
  { key: 'gore', label: { en: 'Gore', ru: 'Жестокость' } },
  { key: 'sex_act', label: { en: 'Sex', ru: 'Секс' } },
  { key: 'nudity', label: { en: 'Nudity', ru: 'Нагота' } },
  { key: 'profanity', label: { en: 'Profanity', ru: 'Мат' } },
  { key: 'drugs', label: { en: 'Drugs', ru: 'Наркотики' } },
  { key: 'child_risk', label: { en: 'Child Risk', ru: 'Дети' } },
]

export default function SceneHeatmap({ scenes }: SceneHeatmapProps) {
  const getColor = (value: number) => {
    if (value > 0.7) return 'bg-red-600'
    if (value > 0.5) return 'bg-orange-500'
    if (value > 0.3) return 'bg-yellow-400'
    if (value > 0.1) return 'bg-blue-400'
    return 'bg-gray-200 dark:bg-gray-700'
  }

  const maxScenesPerRow = 20

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Scene Heatmap
      </h3>

      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {CATEGORIES.map((category) => (
            <div key={category.key} className="mb-2">
              <div className="flex items-center gap-2">
                <div className="w-24 text-sm font-medium text-gray-700 dark:text-gray-300">
                  {category.label.en}
                </div>
                <div className="flex gap-0.5">
                  {scenes.slice(0, maxScenesPerRow).map((scene) => {
                    const value = scene[category.key as keyof Scene] as number
                    const colorClass = getColor(value)

                    return (
                      <div
                        key={`${scene.id}-${category.key}`}
                        className={`w-6 h-6 ${colorClass} hover:ring-2 hover:ring-indigo-500 rounded transition-all cursor-pointer`}
                        title={`Scene ${scene.scene_id}: ${category.label.en} = ${(value * 100).toFixed(0)}%`}
                      />
                    )
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-700 dark:text-gray-300">Legend:</span>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">0-10%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-blue-400 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">10-30%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-yellow-400 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">30-50%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-orange-500 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">50-70%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-red-600 rounded"></div>
            <span className="text-gray-600 dark:text-gray-400">70-100%</span>
          </div>
        </div>
      </div>
    </div>
  )
}
