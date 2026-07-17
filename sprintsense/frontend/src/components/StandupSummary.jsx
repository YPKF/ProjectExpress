import React, { useState } from 'react'
import { getSprintAudio } from '../services/api'

export default function StandupSummary({ summary, sprintId }) {
  const [audioUrl, setAudioUrl] = useState(null)
  const [audioLoading, setAudioLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  const handlePlayAudio = async () => {
    if (!sprintId) return
    setAudioLoading(true)
    try {
      const data = await getSprintAudio(sprintId)
      if (data.success && data.filepath) {
        // The audio path is server-side; we proxy it through the API
        setAudioUrl(`/audio/${data.filepath.split('/').pop()}`)
      }
    } catch {
      // If audio generation fails, show an alert
      alert('Voice summary generation failed. Ensure gTTS is installed.')
    } finally {
      setAudioLoading(false)
    }
  }

  const handleCopy = async () => {
    if (!summary) return
    try {
      await navigator.clipboard.writeText(summary)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea')
      textarea.value = summary
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (!summary) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">🗣️</div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">No Standup Summary</h2>
        <p className="text-gray-500">Run a sprint analysis first to generate the daily standup.</p>
      </div>
    )
  }

  // Format the markdown-like summary for display
  const formattedLines = summary.split('\n').map((line, i) => {
    if (line.startsWith('*') && line.endsWith('*')) {
      return <p key={i} className="text-lg font-semibold text-gray-900 mt-4 mb-2">{line.slice(1, -1)}</p>
    }
    if (line.startsWith('•') || line.startsWith('  •')) {
      return <li key={i} className="text-gray-700 ml-4 mb-1">{line.trim()}</li>
    }
    if (line.trim() === '') {
      return <div key={i} className="h-2" />
    }
    return <p key={i} className="text-gray-700">{line}</p>
  })

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">🗣️ Standup Summary</h2>
          <p className="text-sm text-gray-500 mt-1">
            AI-generated daily standup from sprint data
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-1.5"
          >
            {copied ? (
              <>✅ Copied!</>
            ) : (
              <>📋 Copy</>
            )}
          </button>
          <button
            onClick={handlePlayAudio}
            disabled={audioLoading || !sprintId}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5"
          >
            {audioLoading ? '⏳' : '🔊'} {audioLoading ? 'Generating...' : 'Play Audio'}
          </button>
        </div>
      </div>

      {/* Summary Content */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <div className="prose prose-sm max-w-none">
          {formattedLines}
        </div>
      </div>

      {/* Audio Player */}
      {audioUrl && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">🔊 Voice Summary</p>
          <audio controls className="w-full">
            <source src={audioUrl} type="audio/mpeg" />
            Your browser does not support the audio element.
          </audio>
        </div>
      )}
    </div>
  )
}
