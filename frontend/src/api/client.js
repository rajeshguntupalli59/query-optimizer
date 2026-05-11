import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const connections = {
  list:   ()       => api.get('/connections').then(r => r.data),
  add:    (body)   => api.post('/connections', body).then(r => r.data),
  remove: (id)     => api.delete(`/connections/${id}`),
  test:   (id)     => api.post(`/connections/${id}/test`).then(r => r.data),
}

export const explain = {
  run: (body) => api.post('/explain', body).then(r => r.data),
}

export const indexes = {
  recommend: (body) => api.post('/indexes/recommend', body).then(r => r.data),
}

export const slowQueries = {
  list:  (connId, params) => api.get(`/slow-queries/${connId}`, { params }).then(r => r.data),
  reset: (connId)         => api.post(`/slow-queries/${connId}/reset`).then(r => r.data),
}

export const rewriter = {
  analyze: (sql) => api.post('/rewrite', { sql }).then(r => r.data),
}

export const aiAssistant = {
  analyze:    (body)  => api.post('/ai/analyze', body).then(r => r.data),
  getConfig:  ()      => api.get('/ai/config').then(r => r.data),
  saveConfig: (body)  => api.put('/ai/config', body).then(r => r.data),
}
