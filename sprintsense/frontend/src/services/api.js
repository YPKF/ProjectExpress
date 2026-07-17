/**
 * SprintSense API service
 * Handles all communication with the FastAPI backend.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: '/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Check backend health.
 * @returns {Promise<{status: string, version: string}>}
 */
export async function checkHealth() {
  const { data } = await api.get('/health')
  return data
}

/**
 * Trigger a full sprint analysis.
 * @param {string} [sprintId] - Optional sprint ID
 * @param {string} [dashboardUrl] - Optional dashboard URL
 * @returns {Promise<object>} Analysis results
 */
export async function analyzeSprint(sprintId = null, dashboardUrl = null) {
  const { data } = await api.post('/api/sprint/analyze', {
    sprint_id: sprintId,
    dashboard_url: dashboardUrl,
  })
  return data
}

/**
 * Get sprint status and metrics.
 * @param {string} sprintId - Sprint ID
 * @returns {Promise<object>} Sprint status
 */
export async function getSprintStatus(sprintId) {
  const { data } = await api.get(`/api/sprint/${sprintId}`)
  return data
}

/**
 * Get the markdown sprint report.
 * @param {string} sprintId - Sprint ID
 * @returns {Promise<{markdown: string, report: object}>}
 */
export async function getSprintReport(sprintId) {
  const { data } = await api.get(`/api/sprint/${sprintId}/report`)
  return data
}

/**
 * Get voice summary audio file info.
 * @param {string} sprintId - Sprint ID
 * @returns {Promise<{filepath: string}>}
 */
export async function getSprintAudio(sprintId) {
  const { data } = await api.get(`/api/sprint/${sprintId}/audio`)
  return data
}

/**
 * Generate a sprint retrospective.
 * @param {string} [sprintId] - Optional sprint ID
 * @returns {Promise<{retrospective: string}>}
 */
export async function generateRetrospective(sprintId = null) {
  const { data } = await api.post('/api/sprint/retrospective', {
    sprint_id: sprintId,
  })
  return data
}

/**
 * Get all current blockers.
 * @param {string} [sprintId] - Optional sprint ID
 * @returns {Promise<{blockers: string[], total_blockers: number}>}
 */
export async function getBlockers(sprintId = null) {
  const params = sprintId ? { sprint_id: sprintId } : {}
  const { data } = await api.get('/api/blockers', { params })
  return data
}

/**
 * Get velocity and prediction.
 * @param {string} [sprintId] - Optional sprint ID
 * @returns {Promise<object>} Velocity data
 */
export async function getVelocity(sprintId = null) {
  const params = sprintId ? { sprint_id: sprintId } : {}
  const { data } = await api.get('/api/velocity', { params })
  return data
}

export default api
