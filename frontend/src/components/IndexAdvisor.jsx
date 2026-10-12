import { useState } from 'react'
import { indexes as api } from '../api/client'
import SqlEditor from './SqlEditor'
import { Copy, CheckCheck, TrendingUp, Table, FlaskConical, X } from 'lucide-react'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button onClick={copy} className="p-1 text-gray-500 hover:text-gray-200 transition" title="Copy DDL">
      {copied ? <CheckCheck size={14} className="text-green-400" /> : <Copy size={14} />}
    </button>
  )
}

const BENEFIT_COLOR = {
  High: 'text-red-300 bg-red-950/40 border-red-800/50',
  'Medium-High': 'text-orange-300 bg-orange-950/40 border-orange-800/50',
  Medium: 'text-yellow-300 bg-yellow-950/40 border-yellow-800/50',
  Low: 'text-gray-400 bg-gray-800/40 border-gray-700',
}

function benefitTag(text) {
  for (const key of Object.keys(BENEFIT_COLOR)) {
    if (text.startsWith(key)) return key
  }
  return 'Low'
}

export default function IndexAdvisor({ connectionId }) {
  const [sql, setSql]       = useState('SELECT * FROM orders WHERE customer_id = $1 ORDER BY created_at DESC;')
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')
  const [recs, setRecs]     = useState(null)
  const [impact, setImpact] = useState({})   // recIdx -> {loading, result, error}

  async function run() {
    if (!connectionId) { setError('Select a connection first'); return }
    setLoading(true); setError(''); setRecs(null); setImpact({})
    try {
      const data = await api.recommend({ connection_id: connectionId, sql })
      setRecs(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  async function testImpact(i, rec) {
    setImpact(prev => ({ ...prev, [i]: { loading: true } }))
    try {
      const result = await api.testImpact({ connection_id: connectionId, sql, ddl: rec.ddl })
      setImpact(prev => ({ ...prev, [i]: { loading: false, result } }))
    } catch (e) {
      setImpact(prev => ({ ...prev, [i]: { loading: false, error: e.response?.data?.detail || e.message } }))
    }
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="h-52 shrink-0">
        <SqlEditor value={sql} onChange={setSql} onRun={run} loading={loading} error={error} label="Analyze Indexes" />
      </div>

      {recs !== null && (
        <div className="flex flex-col gap-3 overflow-y-auto flex-1">
          {recs.length === 0 ? (
            <div className="bg-green-950/30 border border-green-800/40 rounded-lg p-4 text-green-300 text-sm">
              No obvious missing indexes detected for this query.
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-400">{recs.length} recommendation{recs.length > 1 ? 's' : ''} found</p>
              {recs.map((rec, i) => {
                const tag = benefitTag(rec.estimated_benefit)
                return (
                  <div key={i} className="bg-gray-800 rounded-lg border border-gray-700 p-4 flex flex-col gap-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <Table size={14} className="text-blue-400 shrink-0" />
                        <span className="font-mono text-sm text-white">{rec.table}</span>
                        {rec.columns.length > 0 && (
                          <span className="text-gray-400 text-xs">({rec.columns.join(', ')})</span>
                        )}
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded border ${BENEFIT_COLOR[tag] || BENEFIT_COLOR.Low}`}>
                        {tag}
                      </span>
                    </div>
                    <p className="text-sm text-gray-300">{rec.reason}</p>
                    <div className="flex items-center gap-2">
                      <TrendingUp size={12} className="text-gray-500 shrink-0" />
                      <p className="text-xs text-gray-400 italic">{rec.estimated_benefit}</p>
                    </div>
                    {rec.ddl && !rec.ddl.startsWith('--') && (
                      <div className="bg-gray-900 rounded p-3 flex items-start justify-between gap-2 border border-gray-700">
                        <pre className="text-xs font-mono text-green-300 whitespace-pre-wrap break-all">{rec.ddl}</pre>
                        <CopyButton text={rec.ddl} />
                      </div>
                    )}
                    {rec.ddl?.startsWith('--') && (
                      <p className="text-xs text-gray-500 italic">{rec.ddl}</p>
                    )}
                    {rec.ddl && !rec.ddl.startsWith('--') && (
                      <div>
                        <button
                          onClick={() => testImpact(i, rec)}
                          disabled={impact[i]?.loading}
                          className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-purple-700/60 bg-purple-950/40 text-purple-300 hover:bg-purple-900/50 transition disabled:opacity-50"
                        >
                          <FlaskConical size={13} />
                          {impact[i]?.loading ? 'Testing…' : 'Test impact'}
                        </button>
                        <p className="text-[11px] text-gray-600 mt-1">Creates the index, measures before/after, then drops it.</p>
                        {impact[i]?.error && (
                          <p className="text-xs text-red-400 mt-2">{impact[i].error}</p>
                        )}
                        {impact[i]?.result && (
                          <ImpactResult result={impact[i].result}
                            onClose={() => setImpact(prev => { const n = { ...prev }; delete n[i]; return n })} />
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </>
          )}
        </div>
      )}
    </div>
  )
}

function ImpactResult({ result, onClose }) {
  const { before, after, improvement_pct, plan_changed, verdict } = result
  const good = verdict === 'faster'
  const fmt = (v, unit) => (v === null || v === undefined) ? '—' : `${Number(v).toFixed(2)}${unit}`
  return (
    <div className="mt-2 bg-gray-900 rounded-lg border border-gray-700 p-3">
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs font-bold uppercase tracking-wide ${good ? 'text-green-400' : 'text-yellow-400'}`}>
          {good ? `✓ ${improvement_pct}% faster` : `No meaningful change (${verdict})`}
        </span>
        <button onClick={onClose} className="text-gray-600 hover:text-gray-300"><X size={13} /></button>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div className="bg-gray-800 rounded p-2">
          <p className="text-gray-500 mb-1">Before</p>
          <p className="font-mono text-gray-200">{fmt(before.execution_ms, ' ms')}</p>
          <p className="text-gray-600 font-mono text-[10px] mt-0.5">{before.node_type}</p>
        </div>
        <div className="bg-gray-800 rounded p-2">
          <p className="text-gray-500 mb-1">After index</p>
          <p className="font-mono text-gray-200">{fmt(after.execution_ms, ' ms')}</p>
          <p className="text-gray-600 font-mono text-[10px] mt-0.5">{after.node_type}</p>
        </div>
        <div className="bg-gray-800 rounded p-2">
          <p className="text-gray-500 mb-1">Plan cost</p>
          <p className="font-mono text-gray-200">{fmt(before.total_cost, '')} → {fmt(after.total_cost, '')}</p>
          <p className="text-gray-600 text-[10px] mt-0.5">{plan_changed ? 'plan changed' : 'same plan shape'}</p>
        </div>
      </div>
      <p className="text-[11px] text-gray-600 mt-2">Index <span className="font-mono">{result.index}</span> was created, measured, and dropped automatically.</p>
    </div>
  )
}
