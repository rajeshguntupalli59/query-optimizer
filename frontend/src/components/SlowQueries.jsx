import { useState } from 'react'
import { slowQueries as api } from '../api/client'
import { RefreshCw, Trash2, Loader2, Clock, BarChart2 } from 'lucide-react'

function ms(v) {
  if (v == null) return '—'
  return v >= 1000 ? `${(v / 1000).toFixed(2)}s` : `${v.toFixed(2)}ms`
}

function Bar({ value, max, color = 'bg-blue-500' }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-700 rounded h-1.5">
        <div className={`h-1.5 rounded ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono w-16 text-right text-gray-400">{ms(value)}</span>
    </div>
  )
}

export default function SlowQueries({ connectionId }) {
  const [queries, setQueries] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [limit, setLimit]     = useState(20)
  const [minCalls, setMinCalls] = useState(1)
  const [selected, setSelected] = useState(null)

  const maxMean = queries ? Math.max(...queries.map(q => q.mean_time_ms ?? 0)) : 1

  async function load() {
    if (!connectionId) { setError('Select a connection first'); return }
    setLoading(true); setError('')
    try {
      const data = await api.list(connectionId, { limit, min_calls: minCalls })
      if (data[0]?.error) { setError(data[0].error); setQueries(null) }
      else setQueries(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  async function reset() {
    if (!connectionId) return
    await api.reset(connectionId)
    setQueries(null)
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="flex items-center gap-3 flex-wrap">
        <label className="flex items-center gap-2 text-sm text-gray-400">
          Top
          <input
            type="number" value={limit} onChange={e => setLimit(Number(e.target.value))}
            min={1} max={100}
            className="w-16 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-center focus:outline-none"
          />
          queries, min
          <input
            type="number" value={minCalls} onChange={e => setMinCalls(Number(e.target.value))}
            min={1}
            className="w-16 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-center focus:outline-none"
          />
          calls
        </label>
        <button
          onClick={load} disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded text-sm transition"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          Load
        </button>
        <button
          onClick={reset}
          className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm transition"
          title="Reset pg_stat_statements"
        >
          <Trash2 size={14} /> Reset stats
        </button>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </div>

      {queries && (
        <div className="flex flex-col gap-2 overflow-y-auto flex-1">
          {queries.length === 0 && (
            <p className="text-gray-500 text-sm">No queries found matching the filter.</p>
          )}
          {queries.map((q, i) => (
            <div
              key={i}
              className={`rounded-lg border p-3 cursor-pointer transition ${
                selected === i ? 'border-blue-500 bg-blue-950/30' : 'border-gray-700 bg-gray-800/60 hover:border-gray-500'
              }`}
              onClick={() => setSelected(selected === i ? null : i)}
            >
              <div className="flex items-start justify-between gap-4 mb-2">
                <pre className="text-xs font-mono text-gray-300 whitespace-pre-wrap break-all line-clamp-2">
                  {q.query?.trim().slice(0, 200)}{q.query?.length > 200 ? '…' : ''}
                </pre>
                <div className="shrink-0 flex flex-col items-end gap-1">
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <BarChart2 size={11} /> {q.calls?.toLocaleString()} calls
                  </span>
                  <span className="text-xs text-cyan-400 flex items-center gap-1">
                    <Clock size={11} /> {ms(q.mean_time_ms)} avg
                  </span>
                </div>
              </div>
              <Bar value={q.mean_time_ms} max={maxMean} color={q.mean_time_ms > maxMean * 0.7 ? 'bg-red-500' : q.mean_time_ms > maxMean * 0.3 ? 'bg-yellow-500' : 'bg-blue-500'} />

              {selected === i && (
                <div className="mt-3 grid grid-cols-3 gap-3">
                  {[
                    ['Total Time', ms(q.total_time_ms)],
                    ['Min Time', ms(q.min_time_ms)],
                    ['Max Time', ms(q.max_time_ms)],
                    ['Rows', q.rows?.toLocaleString()],
                    ['Cache Hit %', q.hit_percent != null ? `${q.hit_percent?.toFixed(1)}%` : '—'],
                    ['Calls', q.calls?.toLocaleString()],
                  ].map(([label, val]) => (
                    <div key={label} className="bg-gray-900 rounded p-2 border border-gray-700">
                      <p className="text-xs text-gray-500">{label}</p>
                      <p className="text-sm font-mono text-white">{val ?? '—'}</p>
                    </div>
                  ))}
                  <div className="col-span-3 bg-gray-900 rounded p-3 border border-gray-700">
                    <p className="text-xs text-gray-500 mb-1">Full Query</p>
                    <pre className="text-xs font-mono text-gray-300 whitespace-pre-wrap break-all">{q.query}</pre>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
