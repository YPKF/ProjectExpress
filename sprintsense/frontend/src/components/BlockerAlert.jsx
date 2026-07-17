import React, { useState, useEffect } from 'react'
import { getBlockers } from '../services/api'

function BlockerCard({ blocker, index }) {
  // Extract ticket ID if present
  const ticketMatch = blocker.match(/\[?([A-Z]+-\d+)\]?/)
  const ticketId = ticketMatch ? ticketMatch[1] : null

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start gap-3">
        <span className="text-red-500 mt-0.5">🔴</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {ticketId && (
              <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-mono rounded">
                {ticketId}
              </span>
            )}
            <span className="text-xs text-gray-400">#{index + 1}</span>
          </div>
          <p className="text-sm text-red-800 mt-1">{blocker}</p>
        </div>
      </div>
    </div>
  )
}

export default function BlockerAlert({ blockers: initialBlockers }) {
  const [blockers, setBlockers] = useState(initialBlockers || [])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (initialBlockers) {
      setBlockers(initialBlockers)
    } else {
      fetchBlockers()
    }
  }, [initialBlockers])

  async function fetchBlockers() {
    setLoading(true)
    try {
      const data = await getBlockers()
      setBlockers(data.blockers || [])
    } catch {
      // Keep existing values
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">🚨 Blocker Alerts</h2>
          <p className="text-sm text-gray-500 mt-1">
            {blockers.length > 0
              ? `${blockers.length} blocker(s) detected across Jira, GitHub, and Slack`
              : 'No blockers detected — sprint is on track'}
          </p>
        </div>
        <button
          onClick={fetchBlockers}
          disabled={loading}
          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

      {blockers.length > 0 ? (
        <div className="grid gap-3">
          {blockers.map((blocker, i) => (
            <BlockerCard key={i} blocker={blocker} index={i} />
          ))}
        </div>
      ) : (
        <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
          <div className="text-4xl mb-3">✅</div>
          <h3 className="text-lg font-semibold text-green-800">All Clear</h3>
          <p className="text-green-600 mt-1">No blockers detected in the current sprint.</p>
        </div>
      )}
    </div>
  )
}
