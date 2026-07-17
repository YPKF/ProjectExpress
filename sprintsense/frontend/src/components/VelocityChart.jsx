import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

// Sample data for the burndown chart
// In production, this would come from the API
const generateSampleData = (velocity) => {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const totalPoints = velocity?.total_points || 40
  const idealPerDay = totalPoints / days.length

  let currentActual = totalPoints
  let currentIdeal = totalPoints

  return days.map((day, i) => {
    currentIdeal = Math.max(0, totalPoints - idealPerDay * (i + 1))
    // Simulate actual progress (slightly behind ideal for realism)
    const actualDrop = idealPerDay * (0.5 + Math.random() * 0.8)
    currentActual = Math.max(0, i === 0 ? totalPoints : currentActual - actualDrop)

    return {
      day,
      ideal: Math.round(currentIdeal * 10) / 10,
      actual: Math.round(currentActual * 10) / 10,
    }
  })
}

export default function VelocityChart({ velocity }) {
  const data = generateSampleData(velocity)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">📈 Sprint Velocity</h2>
        <p className="text-sm text-gray-500 mt-1">
          Ideal burndown vs. actual progress
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Velocity', value: velocity?.velocity ?? '—', unit: 'pts', color: 'text-blue-600' },
          { label: 'Total Points', value: velocity?.total_points ?? '—', unit: 'pts', color: 'text-gray-900' },
          {
            label: 'Completion',
            value: velocity?.completion_probability != null
              ? `${Math.round(velocity.completion_probability * 100)}`
              : '—',
            unit: '%',
            color: velocity?.completion_probability > 0.6 ? 'text-green-600' : 'text-yellow-600',
          },
          {
            label: 'Risk',
            value: velocity?.risk_level ?? '—',
            color: velocity?.risk_level === 'LOW' ? 'text-green-600'
              : velocity?.risk_level === 'HIGH' ? 'text-red-600'
              : 'text-yellow-600',
          },
        ].map((stat, i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <p className="text-xs text-gray-500 mb-1">{stat.label}</p>
            <p className={`text-xl font-bold ${stat.color}`}>
              {stat.value}
              {stat.unit && <span className="text-sm font-normal text-gray-400 ml-1">{stat.unit}</span>}
            </p>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="day"
              stroke="#9ca3af"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              stroke="#9ca3af"
              fontSize={12}
              tickLine={false}
              label={{ value: 'Story Points', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af', fontSize: 12 } }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="ideal"
              stroke="#9ca3af"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Ideal Burndown"
            />
            <Line
              type="monotone"
              dataKey="actual"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 4, fill: '#3b82f6', strokeWidth: 0 }}
              activeDot={{ r: 6 }}
              name="Actual Progress"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {velocity?.summary && (
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
          <p className="text-sm text-blue-800">{velocity.summary}</p>
        </div>
      )}
    </div>
  )
}
