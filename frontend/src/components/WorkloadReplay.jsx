import { useState, useEffect } from 'react'
import { workload as api, connections } from '../api/client'
import { Play, Database, Trash2, Eye, ChevronDown, ShieldCheck, AlertTriangle } from 'lucide-react'

const STATUS = {
  ok:      { label: 'OK',      cls: 'text-green-300 bg-green-950/50 border-green-800/60' },
  slower:  { label: 'SLOWER',  cls: 'text-orange-300 bg-orange-950/50 border-orange-800/60' },
  failed:  { label: 'FAILED',  cls: 'text-red-300 bg-red-950/50 border-red-800/60' },
  errors:  { label: 'ERRORS',  cls: 'text-yellow-300 bg-yellow-950/50 border-yellow-800/60' },
  blocked: { label: 'BLOCKED', cls: 'text-indigo-300 bg-indigo-950/50 border-indigo-800/60' },
}

function StatusTag({ s }) {
  const st = STATUS[s] || STATUS.ok
  return <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${st.cls}`}>{st.label}</span>
}

export default function WorkloadReplay({ connectionId }) {
  const [conns, setConns] = useState([])
  const [workloads, setWorkloads] = useState([])
  const [cap, setCap] = useState({ source: '', name: '', limit: 50 })
  const [rep, setRep] = useState({ workload: '', target: '', iterations: 3, concurrency: 4, safe: true })
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState('')
  const [report, setReport] = useState(null)
  const [detail, setDetail] = useState(null)

  const refresh = async () => {
    setWorkloads(await api.list())
    setConns(await connections.list())
  }
  useEffect(() => { refresh() }, [])
  useEffect(() => { if (connectionId) setRep(r => ({ ...r, target: r.target || connectionId })) }, [connectionId])

  async function doCapture() {
    if (!cap.source || !cap.name) { setError('Pick a source connection and name the workload.'); return }
    setBusy('cap'); setError('')
    try {
      const w = await api.capture({ source_connection_id: cap.source, name: cap.name, limit: Number(cap.limit) })
      setCap({ source: '', name: '', limit: 50 })
      await refresh()
      setError('')
      alert(`Captured ${w.query_count} queries into "${w.name}"`)
    } catch (e) { setError(e.response?.data?.detail || e.message) }
    setBusy(null)
  }

  async function doReplay() {
    if (!rep.workload || !rep.target) { setError('Pick a workload and a target connection.'); return }
    setBusy('rep'); setError(''); setReport(null)
    try {
      const r = await api.replay({
        workload_id: rep.workload, target_connection_id: rep.target,
        iterations: Number(rep.iterations), concurrency: Number(rep.concurrency), safe_mode: rep.safe,
      })
      setReport(r)
    } catch (e) { setError(e.response?.data?.detail || e.message) }
    setBusy(null)
  }

  const sum = report?.summary
  const cards = sum && [
    ['Queries', sum.total, 'text-gray-100'], ['OK', sum.ok, 'text-green-300'],
    ['Slower ≥50%', sum.slower, 'text-orange-300'], ['Failed', sum.failed, 'text-red-300'],
    ['Errors', sum.errors, 'text-yellow-300'], ['Blocked', sum.blocked, 'text-indigo-300'],
  ]

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white flex items-center gap-2"><Play size={16} className="text-blue-400" /> Workload Replay</h2>
        <p className="text-xs text-gray-500 mt-1">Capture a production workload, replay it against staging, and see what breaks before go-live.</p>
      </div>

      {error && <div className="text-xs text-red-300 bg-red-950/40 border border-red-800/50 rounded-lg px-4 py-2.5">{error}</div>}

      {/* capture */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-white mb-1">1 · Capture workload</h3>
        <p className="text-xs text-gray-500 mb-4">Top queries by total time from <span className="font-mono">pg_stat_statements</span> / <span className="font-mono">dm_exec_query_stats</span>.</p>
        <div className="flex gap-3 flex-wrap items-end">
          <label className="text-xs text-gray-400">Source
            <select value={cap.source} onChange={e => setCap({ ...cap, source: e.target.value })}
              className="block mt-1 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 min-w-[200px]">
              <option value="">— pick connection —</option>
              {conns.map(c => <option key={c.id} value={c.id}>{c.name} ({c.db_type})</option>)}
            </select></label>
          <label className="text-xs text-gray-400">Name
            <input value={cap.name} onChange={e => setCap({ ...cap, name: e.target.value })} placeholder="prod-morning-peak"
              className="block mt-1 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 min-w-[180px]" /></label>
          <label className="text-xs text-gray-400">Top N
            <input type="number" value={cap.limit} onChange={e => setCap({ ...cap, limit: e.target.value })}
              className="block mt-1 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 w-20" /></label>
          <button onClick={doCapture} disabled={busy === 'cap'}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold px-5 py-2 rounded-lg transition">
            {busy === 'cap' ? 'Capturing…' : 'Capture'}</button>
        </div>
      </div>

      {/* workloads */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-white mb-3">2 · Saved workloads</h3>
        {workloads.length === 0 && <p className="text-xs text-gray-600">No workloads yet.</p>}
        <div className="space-y-2">
          {workloads.map(w => (
            <div key={w.id} className="flex items-center gap-3 bg-gray-950/60 border border-gray-800 rounded-lg px-4 py-2.5">
              <Database size={13} className="text-gray-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-gray-200">{w.name}</p>
                <p className="text-[11px] text-gray-500">{w.query_count} queries · from {w.source_name} · {new Date(w.captured_at).toLocaleString()}</p>
              </div>
              <button onClick={async () => setDetail(await api.get(w.id))} title="View queries"
                className="p-1.5 text-gray-500 hover:text-gray-200 transition"><Eye size={14} /></button>
              <button onClick={() => { setRep({ ...rep, workload: w.id }); setError('') }} title="Select for replay"
                className="p-1.5 text-gray-500 hover:text-blue-300 transition"><Play size={14} /></button>
              <button onClick={async () => { await api.remove(w.id); refresh() }} title="Delete"
                className="p-1.5 text-gray-500 hover:text-red-300 transition"><Trash2 size={14} /></button>
            </div>))}
        </div>
        {detail && (
          <div className="mt-4 bg-gray-950 border border-gray-800 rounded-lg p-4 max-h-64 overflow-auto">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold text-white">{detail.name} — {detail.query_count} queries</p>
              <button onClick={() => setDetail(null)} className="text-xs text-gray-500 hover:text-gray-300">Close</button>
            </div>
            {detail.queries.map((q, i) => (
              <p key={i} className="font-mono text-[11px] text-gray-400 border-t border-gray-800/60 py-1.5">
                <span className="text-gray-600 mr-2">{i + 1}.</span>{q.sql.slice(0, 200)}
                <span className="text-gray-600 ml-2">⌀ {q.mean_ms.toFixed(2)} ms × {q.calls}</span></p>))}
          </div>)}
      </div>

      {/* replay */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-white mb-4">3 · Replay against staging</h3>
        <div className="flex gap-3 flex-wrap items-end mb-4">
          <label className="text-xs text-gray-400">Workload
            <select value={rep.workload} onChange={e => setRep({ ...rep, workload: e.target.value })}
              className="block mt-1 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 min-w-[200px]">
              <option value="">— pick workload —</option>
              {workloads.map(w => <option key={w.id} value={w.id}>{w.name} ({w.query_count})</option>)}
            </select></label>
          <label className="text-xs text-gray-400">Target (staging)
            <select value={rep.target} onChange={e => setRep({ ...rep, target: e.target.value })}
              className="block mt-1 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 min-w-[200px]">
              <option value="">— pick connection —</option>
              {conns.map(c => <option key={c.id} value={c.id}>{c.name} ({c.db_type})</option>)}
            </select></label>
          <label className="text-xs text-gray-400">Iterations
            <input type="number" min="1" max="20" value={rep.iterations} onChange={e => setRep({ ...rep, iterations: e.target.value })}
              className="block mt-1 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 w-20" /></label>
          <label className="text-xs text-gray-400">Concurrency
            <input type="number" min="1" max="32" value={rep.concurrency} onChange={e => setRep({ ...rep, concurrency: e.target.value })}
              className="block mt-1 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200 w-20" /></label>
          <label className="flex items-center gap-2 text-xs text-gray-300 pb-2 cursor-pointer">
            <input type="checkbox" checked={rep.safe} onChange={e => setRep({ ...rep, safe: e.target.checked })}
              className="accent-blue-600" />
            <span className="flex items-center gap-1"><ShieldCheck size={12} className="text-green-400" /> Safe mode</span>
          </label>
          <button onClick={doReplay} disabled={busy === 'rep'}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold px-5 py-2 rounded-lg transition">
            {busy === 'rep' ? 'Replaying…' : '▶ Run replay'}</button>
        </div>

        {report && (
          <div>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-2 mb-4">
              {cards.map(([label, val, cls]) => (
                <div key={label} className="bg-gray-950/60 border border-gray-800 rounded-lg p-3 text-center">
                  <p className={`text-xl font-extrabold ${cls}`}>{val}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">{label}</p>
                </div>))}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead><tr className="text-left text-gray-500">
                  <th className="pb-2 pr-3 font-medium">Query</th><th className="pb-2 pr-3 font-medium">Baseline</th>
                  <th className="pb-2 pr-3 font-medium">Replay avg</th><th className="pb-2 pr-3 font-medium">Δ</th>
                  <th className="pb-2 font-medium">Status</th>
                </tr></thead>
                <tbody>
                  {report.results.map((r, i) => (
                    <tr key={i} className="border-t border-gray-800/60 align-top">
                      <td className="py-2 pr-3 font-mono text-[11px] text-gray-400 max-w-[420px]">
                        <span className="break-all">{r.sql.slice(0, 160)}{r.sql.length > 160 ? '…' : ''}</span>
                        {r.first_error && <p className="text-red-400/90 mt-1 flex gap-1"><AlertTriangle size={11} className="shrink-0 mt-0.5" />{r.first_error}</p>}
                      </td>
                      <td className="py-2 pr-3 text-gray-400 whitespace-nowrap">{r.baseline_mean_ms} ms</td>
                      <td className="py-2 pr-3 text-gray-300 whitespace-nowrap">{r.replay_mean_ms} ms <span className="text-gray-600">({r.runs}×)</span></td>
                      <td className={`py-2 pr-3 font-bold whitespace-nowrap ${r.delta_pct == null ? 'text-gray-600' : r.delta_pct >= 50 ? 'text-orange-300' : r.delta_pct <= -20 ? 'text-green-300' : 'text-gray-400'}`}>
                        {r.delta_pct == null ? '—' : `${r.delta_pct > 0 ? '+' : ''}${r.delta_pct}%`}</td>
                      <td className="py-2"><StatusTag s={r.status} /></td>
                    </tr>))}
                </tbody>
              </table>
            </div>
          </div>)}
      </div>
    </div>
  )
}
