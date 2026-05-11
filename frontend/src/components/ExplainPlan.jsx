import { useState } from 'react'
import { explain as api } from '../api/client'
import SqlEditor from './SqlEditor'
import { AlertTriangle, Info, ChevronDown, ChevronRight, Zap } from 'lucide-react'

const SEQ_SCAN_COLOR   = 'text-red-400'
const INDEX_SCAN_COLOR = 'text-green-400'
const JOIN_COLOR       = 'text-yellow-400'
const DEFAULT_COLOR    = 'text-blue-400'

function nodeColor(type = '') {
  if (type.includes('Seq Scan'))   return SEQ_SCAN_COLOR
  if (type.includes('Index'))      return INDEX_SCAN_COLOR
  if (type.includes('Join'))       return JOIN_COLOR
  return DEFAULT_COLOR
}

function PlanNode({ node, depth = 0 }) {
  const [open, setOpen] = useState(true)
  const children = node.Plans || []
  const hasChildren = children.length > 0
  const type = node['Node Type'] || ''

  return (
    <div className={`pl-${depth > 0 ? 4 : 0}`} style={{ paddingLeft: depth * 16 }}>
      <div
        className="flex items-start gap-2 py-1 cursor-pointer hover:bg-gray-800/50 rounded px-2 group"
        onClick={() => hasChildren && setOpen(o => !o)}
      >
        <span className="mt-0.5 text-gray-500 w-4 shrink-0">
          {hasChildren ? (open ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : null}
        </span>
        <div className="flex-1 min-w-0">
          <span className={`font-mono font-medium text-sm ${nodeColor(type)}`}>{type}</span>
          {node['Relation Name'] && (
            <span className="text-gray-300 text-sm ml-2">on <span className="font-mono">{node['Relation Name']}</span></span>
          )}
          {node['Index Name'] && (
            <span className="text-gray-400 text-xs ml-2">using <span className="font-mono">{node['Index Name']}</span></span>
          )}
          <div className="flex flex-wrap gap-3 mt-0.5 text-xs text-gray-500">
            <span>cost={node['Startup Cost']?.toFixed(2)}..{node['Total Cost']?.toFixed(2)}</span>
            <span>rows={node['Plan Rows']}</span>
            {node['Actual Total Time'] !== undefined && (
              <span className="text-cyan-400">actual {node['Actual Total Time']?.toFixed(2)}ms, {node['Actual Rows']} rows</span>
            )}
            {node['Filter'] && <span className="text-orange-400 truncate max-w-xs">filter: {node['Filter']}</span>}
          </div>
        </div>
      </div>
      {open && children.map((child, i) => (
        <PlanNode key={i} node={child} depth={depth + 1} />
      ))}
    </div>
  )
}

function Warnings({ warnings }) {
  if (!warnings?.length) return null
  return (
    <div className="flex flex-col gap-2">
      {warnings.map((w, i) => (
        <div key={i} className="flex items-start gap-2 bg-yellow-950/40 border border-yellow-800/50 rounded-lg px-3 py-2 text-sm">
          <AlertTriangle size={14} className="text-yellow-400 mt-0.5 shrink-0" />
          <span className="text-yellow-200">{w.message}</span>
        </div>
      ))}
    </div>
  )
}

export default function ExplainPlan({ connectionId, dbType = 'postgres' }) {
  const [sql, setSql]         = useState('SELECT * FROM your_table WHERE id = 1;')
  const [analyze, setAnalyze] = useState(false)
  const [buffers, setBuffers] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [result, setResult]   = useState(null)

  const isMssql = dbType === 'mssql'

  async function run() {
    if (!connectionId) { setError('Select a connection first'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await api.run({ connection_id: connectionId, sql, analyze, buffers: !isMssql && buffers, verbose: false })
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="flex items-center gap-4 text-sm text-gray-400">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={analyze} onChange={e => setAnalyze(e.target.checked)} className="accent-blue-500" />
          {isMssql ? 'STATISTICS PROFILE (runs the query)' : 'ANALYZE (actually runs the query)'}
        </label>
        {!isMssql && (
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={buffers} onChange={e => setBuffers(e.target.checked)} className="accent-blue-500" disabled={!analyze} />
            BUFFERS
          </label>
        )}
      </div>

      <div className="h-52 shrink-0">
        <SqlEditor value={sql} onChange={setSql} onRun={run} loading={loading} error={error} label="EXPLAIN" />
      </div>

      {result && (
        <div className="flex flex-col gap-4 overflow-y-auto flex-1">
          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              ['Total Cost', result.summary.total_cost?.toFixed(2), 'text-red-300'],
              ['Est. Rows', result.summary.plan_rows, 'text-blue-300'],
              ['Actual Time', result.summary.actual_total_time != null ? `${result.summary.actual_total_time?.toFixed(2)} ms` : '—', 'text-cyan-300'],
              ['Node Type', result.summary.node_type, 'text-purple-300'],
            ].map(([label, val, color]) => (
              <div key={label} className="bg-gray-800 rounded-lg px-4 py-3 border border-gray-700">
                <p className="text-xs text-gray-500">{label}</p>
                <p className={`text-lg font-mono font-semibold ${color}`}>{val ?? '—'}</p>
              </div>
            ))}
          </div>

          <Warnings warnings={result.summary.warnings} />

          {/* Plan tree */}
          <div className="bg-gray-900 rounded-lg border border-gray-700 p-3 overflow-x-auto">
            <p className="text-xs text-gray-500 mb-3 flex items-center gap-1"><Zap size={12} /> Execution Plan</p>
            {result.plan[0]?.Plan && <PlanNode node={result.plan[0].Plan} />}
          </div>
        </div>
      )}
    </div>
  )
}
