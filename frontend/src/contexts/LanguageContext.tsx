import { createContext, useContext, useState, ReactNode } from 'react'

export type Language = 'en' | 'ru'

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string) => string
}

const translations: Record<Language, Record<string, string>> = {
  en: {
    'app.title': 'Script Rating AI',
    'nav.home': 'Home',
    'nav.upload': 'Upload Script',
    'nav.scripts': 'Scripts',
    'script.title': 'Script Title',
    'script.upload': 'Upload',
    'script.analyze': 'Analyze Script',
    'script.analyzing': 'Analyzing...',
    'script.rating': 'Rating',
    'script.scenes': 'scenes',
    'script.uploaded': 'Uploaded',
    'script.not_found': 'Script not found',
    'script.failed_load': 'Failed to load script',
    'script.evidence': 'Evidence from Script',
    'script.analysis_scores': 'Content Analysis Scores',
    'script.high_impact_scenes': 'High-Impact Scenes',
    'script.impact': 'Impact',
    'whatif.title': 'What-If Rating Simulator',
    'whatif.current_rating': 'Current Rating',
    'whatif.describe_modification': 'Describe your modification',
    'whatif.placeholder': 'Example: remove scene 12-13, replace fight with verbal conflict, remove all profanity...',
    'whatif.quick_examples': 'Quick examples:',
    'whatif.run_simulation': 'Run Simulation',
    'whatif.simulating': 'Simulating...',
    'whatif.rating_comparison': 'Rating Comparison',
    'whatif.original': 'Original',
    'whatif.modified': 'Modified',
    'whatif.rating_improved': '✓ Rating improved!',
    'whatif.rating_increased': '✗ Rating increased',
    'whatif.applied_changes': 'Applied Changes',
    'whatif.explanation': 'Explanation',
    'whatif.original_scores': 'Original Scores',
    'whatif.modified_scores': 'Modified Scores',
    'theme.toggle': 'Toggle theme',
    'theme.dark': 'Dark mode',
    'theme.light': 'Light mode',
    'language.select': 'Language',
  },
  ru: {
    'app.title': 'ИИ Оценки Сценариев',
    'nav.home': 'Главная',
    'nav.upload': 'Загрузить сценарий',
    'nav.scripts': 'Сценарии',
    'script.title': 'Название сценария',
    'script.upload': 'Загрузить',
    'script.analyze': 'Анализировать сценарий',
    'script.analyzing': 'Анализ...',
    'script.rating': 'Рейтинг',
    'script.scenes': 'сцен',
    'script.uploaded': 'Загружено',
    'script.not_found': 'Сценарий не найден',
    'script.failed_load': 'Не удалось загрузить сценарий',
    'script.evidence': 'Доказательства из сценария',
    'script.analysis_scores': 'Оценки анализа контента',
    'script.high_impact_scenes': 'Сцены с высоким влиянием',
    'script.impact': 'Влияние',
    'whatif.title': 'Симулятор What-If рейтинга',
    'whatif.current_rating': 'Текущий рейтинг',
    'whatif.describe_modification': 'Опишите изменение',
    'whatif.placeholder': 'Пример: убрать сцену 12-13, заменить драку на словесный конфликт, убрать весь мат...',
    'whatif.quick_examples': 'Быстрые примеры:',
    'whatif.run_simulation': 'Запустить симуляцию',
    'whatif.simulating': 'Симуляция...',
    'whatif.rating_comparison': 'Сравнение рейтингов',
    'whatif.original': 'Оригинал',
    'whatif.modified': 'Изменённый',
    'whatif.rating_improved': '✓ Рейтинг улучшен!',
    'whatif.rating_increased': '✗ Рейтинг увеличен',
    'whatif.applied_changes': 'Применённые изменения',
    'whatif.explanation': 'Объяснение',
    'whatif.original_scores': 'Оригинальные оценки',
    'whatif.modified_scores': 'Изменённые оценки',
    'theme.toggle': 'Переключить тему',
    'theme.dark': 'Тёмная тема',
    'theme.light': 'Светлая тема',
    'language.select': 'Язык',
  },
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('language') as Language | null
    return saved || (navigator.language.startsWith('ru') ? 'ru' : 'en')
  })

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
    localStorage.setItem('language', lang)
  }

  const t = (key: string): string => {
    return translations[language][key] || key
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}
