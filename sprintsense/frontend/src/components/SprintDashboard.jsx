import React from 'react'

function RiskBadge({ level }) {
  const colors = {
    LOW: 'bg-green-50 text-green-700 border-green-200',
    MEDIUM: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    HIGH: 'bg-red-50 text-red-700 border-red-200',
  }
  const icons = { LOW: '✅', MEDIUM: '⚠️', HIGH: '🚨' }
  const cls = colors[level] || colors.MEDIUM

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${cls}`}>
      {icons[level] || '❓'} {level}
    </span>
  )
}

function StatCard({ label, value, unit, color }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color || 'text-gray-900'}`}>
        {value ?? '—'}
        {unit && <span className="text-sm font-normal text-gray-400 ml-1">{unit}</span>}
      </p>
    </div>
  )
}

function ProgressBar({ completed, total }) {
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0
  const barColor = pct >= 75 ? 'bg-green-500' : pct >= 40 ? 'bg-blue-500' : 'bg-yellow-500'

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">Sprint Progress</span>
        <span className="text-sm font-medium text-gray-700">{completed}/{total} tickets</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3">
        <div
          className={`${barColor} h-3 rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <p className="text-right text-xs text-gray-400 mt-1">{pct}% complete</p>
    </div>
  )
}

export default function SprintDashboard({ analysis, velocity, onAnalyze, loading }) {
  if (!analysis && !loading) {
    return (
      <div className="text-center py-20">
        <div className="text-6xl mb-4">📊</div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">No Sprint Data Yet</h2>
        <p className="text-gray-500 mb-6">Click "Analyze Sprint" to run the full intelligence pipeline.</p>
        <button
          onClick={onAnalyze}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          🚀 Analyze Sprint
        </button>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="animate-spin text-4xl mb-4 inline-block">⏳</div>
        <h2 className="text-xl font-semibold text-gray-700">Analyzing Sprint...</h2>
        <p className="text-gray-500 mt-2">Running Jira, GitHub, Slack, Vision, and Prediction agents.</p>
        <div className="mt-8 max-w-md mx-auto">
          <div className="w-full bg-gray-100 rounded-full h-2">
            <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Sprint Header */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{analysis.sprint_name || 'Sprint Analysis'}</h2>
            <p className="text-sm text-gray-500 mt-1">ID: {analysis.sprint_id}</p>
          </div>
          <RiskBadge level={analysis.risk_level} />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Tickets" value={analysis.total_tickets} color="text-gray-900" />
        <StatCard
          label="Velocity"
          value={velocity?.velocity ?? analysis.velocity}
          unit="pts"
          color="text-blue-600"
        />
        <StatCard
          label="Completion"
          value={velocity?.completion_probability != null
            ? `${Math.round(velocity.completion_probability * 100)}`
            : analysis.completion_probability != null
              ? `${Math.round(analysis.completion_probability * 100)}`
              : '—'}
          unit="%"
          color="text-purple-600"
        />
        <StatCard
          label="Blockers"
          value={analysis.blockers?.length ?? 0}
          color={(analysis.blockers?.length ?? 0) > 0 ? 'text-red-600' : 'text-green-600'}
        />
      </div>

      {/* Progress Bar */}
      {analysis.total_tickets > 0 && (
        <ProgressBar
          completed={analysis.completed_tickets ?? 0}
          total={analysis.total_tickets}
        />
      )}
    </div>
  )
}
