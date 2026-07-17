import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { generateRetrospective, getSprintReport } from '../services/api'

export default function RetrospectiveViewer({ sprintId }) {
  const [retroText, setRetroText] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await generateRetrospective(sprintId)
      setRetroText(data.retrospective)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!retroText) return
    const blob = new Blob([retroText], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `retrospective-${sprintId || 'sprint'}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (!retroText && !loading) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">🔄</div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Sprint Retrospective</h2>
        <p className="text-gray-500 mb-6">
          Generate an AI-powered retrospective document analyzing what went well,
          what could be improved, and actionable insights.
        </p>
        <button
          onClick={handleGenerate}
          className="px-6 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition-colors"
        >
          {loading ? '⏳ Generating...' : '🔄 Generate Retrospective'}
        </button>
        {error && (
          <p className="text-red-600 text-sm mt-4">⚠️ {error}</p>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="animate-spin text-4xl mb-4 inline-block">🔄</div>
        <h2 className="text-xl font-semibold text-gray-700">Generating Retrospective...</h2>
        <p className="text-gray-500 mt-2">Analyzing sprint data and creating insights.</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">🔄 Sprint Retrospective</h2>
          <p className="text-sm text-gray-500 mt-1">
            AI-generated analysis from sprint data
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleGenerate}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            🔄 Regenerate
          </button>
          <button
            onClick={handleDownload}
            className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            📥 Download as Markdown
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-8">
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            components={{
              h1: ({ children }) => <h1 className="text-2xl font-bold text-gray-900 mb-4 mt-6 first:mt-0">{children}</h1>,
              h2: ({ children }) => <h2 className="text-xl font-semibold text-gray-800 mb-3 mt-5">{children}</h2>,
              h3: ({ children }) => <h3 className="text-lg font-medium text-gray-800 mb-2 mt-4">{children}</h3>,
              p: ({ children }) => <p className="text-gray-700 mb-3 leading-relaxed">{children}</p>,
              ul: ({ children }) => <ul className="list-disc pl-5 mb-4 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-5 mb-4 space-y-1">{children}</ol>,
              li: ({ children }) => <li className="text-gray-700">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
              hr: () => <hr className="my-6 border-gray-200" />,
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-purple-200 pl-4 py-2 my-4 bg-purple-50 rounded-r-lg">
                  <p className="text-gray-700 italic">{children}</p>
                </blockquote>
              ),
              code: ({ children }) => (
                <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
              ),
            }}
          >
            {retroText}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
