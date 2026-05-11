import { useState } from 'react'
import { indexes as api } from '../api/client'
import SqlEditor from './SqlEditor'
import { Copy, CheckCheck, TrendingUp, Table } from 'lucide-react'

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

  async function run() {
    if (!connectionId) { setError('Select a connection first'); return }
    setLoading(true); setError(''); setRecs(null)
    try {
      const data = await api.recommend({ connection_id: connectionId, sql })
      setRecs(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
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
