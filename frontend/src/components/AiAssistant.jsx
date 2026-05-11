import { useState } from 'react'
import { aiAssistant } from '../api/client'
import SqlEditor from './SqlEditor'
import { Sparkles, AlertTriangle, Lightbulb, Code2, Copy, CheckCheck, Settings } from 'lucide-react'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500) }}
      className="p-1 text-gray-600 hover:text-gray-300 transition"
    >
      {copied ? <CheckCheck size={13} className="text-green-400" /> : <Copy size={13} />}
    </button>
  )
}

export default function AiAssistant({ connectionId, dbType = 'postgres', onGoToSettings }) {
  const [sql, setSql]         = useState('SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id WHERE LOWER(c.email) LIKE \'%@gmail.com\' ORDER BY o.created_at DESC;')
  const [context, setContext] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [result, setResult]   = useState(null)

  async function run() {
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await aiAssistant.analyze({ sql, db_type: dbType || 'postgres', context })
      if (data.error) setError(data.error)
      else setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-5 h-full">
      {/* Context hint */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500">
          Optional context (table sizes, constraints, known issues)
        </label>
        <input
          value={context}
          onChange={e => setContext(e.target.value)}
          placeholder="e.g. orders has 50M rows, customer_id is not indexed"
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm placeholder-gray-600 focus:outline-none focus:border-blue-500 transition"
        />
      </div>

      {/* SQL editor */}
      <div className="h-52 shrink-0">
        <SqlEditor
          value={sql}
          onChange={setSql}
          onRun={run}
          loading={loading}
          error={error}
          label="Analyze with AI"
        />
      </div>

      {/* Not configured state */}
      {error?.includes('not configured') && (
        <div className="flex items-center justify-between bg-yellow-950/40 border border-yellow-800/50 rounded-xl p-4">
          <div>
            <p className="text-sm font-medium text-yellow-300">AI is not configured</p>
            <p className="text-xs text-yellow-700 mt-0.5">Add your AI endpoint and API key in Settings to enable this feature.</p>
          </div>
          <button
            onClick={onGoToSettings}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-yellow-800/60 hover:bg-yellow-700/60 rounded-lg text-yellow-200 transition"
          >
            <Settings size={12} /> Settings
          </button>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="flex flex-col gap-4 overflow-y-auto flex-1">

          {/* Rewritten SQL */}
          {result.rewritten_sql && (
            <div className="rounded-xl border border-emerald-800/50 bg-emerald-950/30 p-4 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                  <Code2 size={14} /> Optimized Query
                </div>
                <CopyButton text={result.rewritten_sql} />
              </div>
              <pre className="text-xs font-mono text-emerald-200 whitespace-pre-wrap break-all leading-relaxed">
                {result.rewritten_sql}
              </pre>
            </div>
          )}

          {/* Explanation */}
          {result.explanation && (
            <div className="rounded-xl border border-blue-800/40 bg-blue-950/20 p-4 flex flex-col gap-1.5">
              <div className="flex items-center gap-2 text-blue-400 text-sm font-medium">
                <Sparkles size={14} /> What changed &amp; why
              </div>
              <p className="text-sm text-gray-300 leading-relaxed">{result.explanation}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Warnings */}
            {result.warnings?.length > 0 && (
              <div className="rounded-xl border border-yellow-800/40 bg-yellow-950/20 p-4 flex flex-col gap-2">
                <div className="flex items-center gap-2 text-yellow-400 text-sm font-medium">
                  <AlertTriangle size={14} /> Warnings
                </div>
                <ul className="flex flex-col gap-1.5">
                  {result.warnings.map((w, i) => (
                    <li key={i} className="text-xs text-yellow-200 flex items-start gap-2">
                      <span className="text-yellow-600 mt-0.5">•</span> {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Tips */}
            {result.tips?.length > 0 && (
              <div className="rounded-xl border border-purple-800/40 bg-purple-950/20 p-4 flex flex-col gap-2">
                <div className="flex items-center gap-2 text-purple-400 text-sm font-medium">
                  <Lightbulb size={14} /> Tuning Tips
                </div>
                <ul className="flex flex-col gap-1.5">
                  {result.tips.map((t, i) => (
                    <li key={i} className="text-xs text-purple-200 flex items-start gap-2">
                      <span className="text-purple-600 mt-0.5">•</span> {t}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
