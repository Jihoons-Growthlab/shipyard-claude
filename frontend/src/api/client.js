// Single HTTP client. Server owns validation/authorization; this only transports.
export class ApiError extends Error {
  constructor(status, body) {
    super(body?.message || `HTTP ${status}`)
    this.status = status
    this.code = body?.code
    this.details = body?.details || {}
  }
}

let tokenProvider = () => null
let onUnauthorized = () => {}
export function configureClient({ getToken, unauthorized }) {
  if (getToken) tokenProvider = getToken
  if (unauthorized) onUnauthorized = unauthorized
}

export async function request(method, path, { body, token } = {}) {
  const headers = { Accept: 'application/json' }
  const bearer = token ?? tokenProvider()
  if (bearer) headers.Authorization = `Bearer ${bearer}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  const data = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) {
    if (res.status === 401 && bearer && token === undefined) onUnauthorized()
    throw new ApiError(res.status, data)
  }
  return data
}

// Binary transport for drawing PDFs (raw body upload, blob download) with the same auth/error handling.
async function binary(method, path, file) {
  const headers = {}
  const bearer = tokenProvider()
  if (bearer) headers.Authorization = `Bearer ${bearer}`
  if (file) headers['Content-Type'] = file.type || 'application/pdf'
  const res = await fetch(path, { method, headers, body: file || undefined })
  if (!res.ok) {
    const data = await res.json().catch(() => null)
    if (res.status === 401 && bearer) onUnauthorized()
    throw new ApiError(res.status, data)
  }
  return file ? res.json() : res.blob()
}

export const api = {
  login: (emp_no, password) => request('POST', '/api/auth/login', { body: { emp_no, password } }),
  verifyOtp: (otpToken, code) => request('POST', '/api/auth/otp/verify', { body: { code }, token: otpToken }),
  register: (form) => request('POST', '/api/auth/register', { body: form }),
  logout: () => request('POST', '/api/auth/logout'),
  me: () => request('GET', '/api/auth/me'),
  menu: () => request('GET', '/api/me/menu'),
  menuAccess: (menu_id) => request('POST', '/api/me/menu-access', { body: { menu_id } }),
  codes: () => request('GET', '/api/codes'),
  // F04 hulls
  hulls: (params = {}) => request('GET', '/api/hulls?' + new URLSearchParams(Object.entries(params).filter(([, v]) => v))),
  hull: (no) => request('GET', `/api/hulls/${encodeURIComponent(no)}`),
  createHull: (body) => request('POST', '/api/hulls', { body }),
  updateHull: (no, body) => request('PATCH', `/api/hulls/${encodeURIComponent(no)}`, { body }),
  deleteHull: (no) => request('DELETE', `/api/hulls/${encodeURIComponent(no)}`),
  milestones: (no) => request('GET', `/api/hulls/${encodeURIComponent(no)}/milestones`),
  saveMilestones: (no, items) => request('PUT', `/api/hulls/${encodeURIComponent(no)}/milestones`, { body: { items } }),
  blocks: (no) => request('GET', `/api/hulls/${encodeURIComponent(no)}/blocks`),
  addBlock: (no, body) => request('POST', `/api/hulls/${encodeURIComponent(no)}/blocks`, { body }),
  deleteBlock: (id) => request('DELETE', `/api/blocks/${id}`),
  hullSummary: (no) => request('GET', `/api/hulls/${encodeURIComponent(no)}/summary`),
  // F05 planning
  procs: () => request('GET', '/api/procs'),
  userOptions: () => request('GET', '/api/users/options'),
  planHulls: () => request('GET', '/api/plan-hulls'),
  plans: (no, blockId) => request('GET', `/api/hulls/${encodeURIComponent(no)}/plans` + (blockId ? `?block_id=${blockId}` : '')),
  createPlan: (no, body) => request('POST', `/api/hulls/${encodeURIComponent(no)}/plans`, { body }),
  updatePlan: (id, body) => request('PATCH', `/api/plans/${id}`, { body }),
  deletePlan: (id) => request('DELETE', `/api/plans/${id}`),
  planDrawings: (id) => request('GET', `/api/plans/${id}/drawings`),
  linkDrawing: (id, drawing_id, required) => request('POST', `/api/plans/${id}/drawings`, { body: { drawing_id, required } }),
  unlinkDrawing: (id, drawingId) => request('DELETE', `/api/plans/${id}/drawings/${drawingId}`),
  // F06 progress
  progressHulls: () => request('GET', '/api/progress-hulls'),
  progressTargets: (no, includeDone) => request('GET', `/api/hulls/${encodeURIComponent(no)}/progress-targets?include_done=${!!includeDone}`),
  planProgress: (id) => request('GET', `/api/plans/${id}/progress`),
  saveProgress: (id, workDt, body) => request('PUT', `/api/plans/${id}/progress/${encodeURIComponent(workDt || '-')}`, { body }),
  deleteProgress: (progressId) => request('DELETE', `/api/progress/${progressId}`),
  // F07 drawings
  drawings: (params = {}) => request('GET', '/api/drawings?' + new URLSearchParams(Object.entries(params).filter(([, v]) => v))),
  drawing: (id) => request('GET', `/api/drawings/${id}`),
  createDrawing: (body) => request('POST', '/api/drawings', { body }),
  updateDrawing: (id, body) => request('PATCH', `/api/drawings/${id}`, { body }),
  deleteDrawing: (id) => request('DELETE', `/api/drawings/${id}`),
  newRevision: (id, change_desc) => request('POST', `/api/drawings/${id}/revisions`, { body: { change_desc } }),
  uploadPdf: (id, rev, file) => binary('POST', `/api/drawings/${id}/revisions/${rev}/pdf?filename=${encodeURIComponent(file.name)}`, file),
  pdfBlob: (id, rev) => binary('GET', `/api/drawings/${id}/revisions/${rev}/pdf`),
  deletePdf: (id, rev) => request('DELETE', `/api/drawings/${id}/revisions/${rev}/pdf`),
  requestApproval: (id, rev, reviewer_emp_no, approver_emp_no) =>
    request('POST', `/api/drawings/${id}/revisions/${rev}/request-approval`, { body: { reviewer_emp_no, approver_emp_no } }),
  issueRevision: (id, rev) => request('POST', `/api/drawings/${id}/revisions/${rev}/issue`),
  linkPlan: (id, plan_id, required) => request('POST', `/api/drawings/${id}/plans`, { body: { plan_id, required } }),
  unlinkPlan: (id, planId) => request('DELETE', `/api/drawings/${id}/plans/${planId}`),
  // F09 users
  users: (params = {}) => request('GET', '/api/users?' + new URLSearchParams(Object.entries(params).filter(([, v]) => v))),
  createUser: (body) => request('POST', '/api/users', { body }),
  updateUser: (emp, body) => request('PATCH', `/api/users/${encodeURIComponent(emp)}`, { body }),
  deleteUser: (emp) => request('DELETE', `/api/users/${encodeURIComponent(emp)}`),
  approveUser: (emp, groups) => request('POST', `/api/users/${encodeURIComponent(emp)}/approve`, { body: { groups } }),
  authGroups: () => request('GET', '/api/auth-groups'),
  // F02 weather
  weather: (region) => request('GET', '/api/weather?region=' + encodeURIComponent(region)),
  // F03 dashboard
  dashboard: () => request('GET', '/api/dashboard/summary'),
  // F08 approvals
  approvalInbox: () => request('GET', '/api/approvals/inbox'),
  approvalHistory: () => request('GET', '/api/approvals/history'),
  decideApproval: (id, result, comment) => request('POST', `/api/approvals/${id}/decision`, { body: { result, comment } }),
}
