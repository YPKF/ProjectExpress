import React, { useState, useEffect, useCallback } from 'react'
import SprintDashboard from './components/SprintDashboard'
import BlockerAlert from './components/BlockerAlert'
import VelocityChart from './components/VelocityChart'
import StandupSummary from './components/StandupSummary'
import RetrospectiveViewer from './components/RetrospectiveViewer'
import { checkHealth, analyzeSprint, getBlockers, getVelocity } from './services/api'

export default function App() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [blockers, setBlockers] = useState([])
  const [velocity, setVelocity] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: 'error' }))
  }, [])

  const handleAnalyze = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await analyzeSprint()
      setAnalysis(result)
      // Fetch additional data
      const [blockerData, velocityData] = await Promise.all([
        getBlockers().catch(() => ({ blockers: [] })),
        getVelocity().catch(() => null),
      ])
      setBlockers(blockerData.blockers || [])
      setVelocity(velocityData)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }, [])

  const isConnected = health?.status === 'ok'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🚀</span>
              <h1 className="text-xl font-bold text-gray-900">SprintSense</h1>
              <span className="text-sm text-gray-500 hidden sm:inline">
                AI Sprint Intelligence
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                isConnected ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`} />
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
              <button
                onClick={handleAnalyze}
                disabled={loading || !isConnected}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Analyze Sprint
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex gap-6 -mb-px">
            {[
              { key: 'dashboard', label: 'Dashboard', icon: '📊' },
              { key: 'blockers', label: 'Blockers', icon: '🚨', count: blockers.length },
              { key: 'velocity', label: 'Velocity', icon: '📈' },
              { key: 'standup', label: 'Standup', icon: '🗣️' },
              { key: 'retro', label: 'Retrospective', icon: '🔄' },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-1 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
                {tab.count > 0 && (
                  <span className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${
                    activeTab === tab.key ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <SprintDashboard analysis={analysis} velocity={velocity} onAnalyze={handleAnalyze} loading={loading} />
        )}
        {activeTab === 'blockers' && (
          <BlockerAlert blockers={blockers} />
        )}
        {activeTab === 'velocity' && (
          <VelocityChart velocity={velocity} />
        )}
        {activeTab === 'standup' && (
          <StandupSummary summary={analysis?.standup_summary} sprintId={analysis?.sprint_id} />
        )}
        {activeTab === 'retro' && (
          <RetrospectiveViewer sprintId={analysis?.sprint_id} />
        )}
      </main>
    </div>
  )
}
