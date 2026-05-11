import { useState } from 'react'
import { rewriter as api } from '../api/client'
import SqlEditor from './SqlEditor'
import { AlertTriangle, Info, CheckCircle, Copy, CheckCheck } from 'lucide-react'

const SEVERITY = {
  high:   { icon: AlertTriangle, color: 'text-red-400',    bg: 'bg-red-950/40 border-red-800/50',    label: 'High' },
  medium: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-950/40 border-yellow-800/50', label: 'Medium' },
  low:    { icon: Info,          color: 'text-blue-400',   bg: 'bg-blue-950/40 border-blue-800/50',   label: 'Low' },
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  function copy() { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500) }
  return (
    <button onClick={copy} className="p-1 text-gray-500 hover:text-gray-200" title="Copy rewritten SQL">
      {copied ? <CheckCheck size={14} className="text-green-400" /> : <Copy size={14} />}
    </button>
  )
}

export default function QueryRewriter() {
  const [sql, setSql]         = useState('SELECT DISTINCT * FROM orders WHERE LOWER(email) = \'test@example.com\' OR status = \'pending\' ORDER BY created_at OFFSET 10000 LIMIT 20;')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [suggestions, setSuggestions] = useState(null)

  async function run() {
    setLoading(true); setError(''); setSuggestions(null)
    try {
      const data = await api.analyze(sql)
      setSuggestions(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="h-52 shrink-0">
        <SqlEditor value={sql} onChange={setSql} onRun={run} loading={loading} error={error} label="Analyze Query" />
      </div>

      {suggestions !== null && (
        <div className="flex flex-col gap-3 overflow-y-auto flex-1">
          {suggestions.length === 0 ? (
            <div className="flex items-center gap-2 bg-green-950/30 border border-green-800/40 rounded-lg p-4 text-green-300 text-sm">
              <CheckCircle size={16} /> No issues found — query looks clean!
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-400">{suggestions.length} issue{suggestions.length > 1 ? 's' : ''} detected</p>
              {suggestions.map((s, i) => {
                const sev = SEVERITY[s.severity] || SEVERITY.low
                const Icon = sev.icon
                return (
                  <div key={i} className={`rounded-lg border p-4 flex flex-col gap-3 ${sev.bg}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Icon size={14} className={sev.color} />
                        <span className={`text-sm font-medium ${sev.color}`}>{s.issue}</span>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded border ${sev.bg} ${sev.color}`}>{sev.label}</span>
                    </div>
                    <p className="text-sm text-gray-300">{s.suggestion}</p>
                    {s.rewritten_sql && (
                      <div className="flex flex-col gap-1">
                        <p className="text-xs text-gray-500">Suggested rewrite:</p>
                        <div className="bg-gray-900 rounded p-3 border border-gray-700 flex items-start gap-2">
                          <pre className="text-xs font-mono text-green-300 whitespace-pre-wrap break-all flex-1">{s.rewritten_sql}</pre>
                          <CopyButton text={s.rewritten_sql} />
                        </div>
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
