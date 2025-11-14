import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import ScriptList from './components/ScriptList'
import ScriptDetail from './components/ScriptDetail'
import UploadScript from './components/UploadScript'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <Link to="/" className="flex items-center px-2 text-gray-900 font-semibold text-lg">
                  Movie Script Rating
                </Link>
                <Link to="/upload" className="flex items-center px-4 text-gray-600 hover:text-gray-900">
                  Upload Script
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<ScriptList />} />
            <Route path="/scripts/:id" element={<ScriptDetail />} />
            <Route path="/upload" element={<UploadScript />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
