import { useState, useEffect } from 'react'
import { connections as api } from '../api/client'
import { Plus, Trash2, CheckCircle, XCircle, Database, Loader2, Server } from 'lucide-react'

const DB_TYPES = [
  { value: 'postgres', label: 'PostgreSQL', defaultPort: 5432 },
  { value: 'mssql',    label: 'SQL Server',  defaultPort: 1433 },
]

const EMPTY = { name: '', db_type: 'postgres', host: 'localhost', port: 5432, database: '', username: 'postgres', password: '' }

const DB_BADGE = {
  postgres: 'bg-blue-900/50 text-blue-300 border-blue-700',
  mssql:    'bg-orange-900/50 text-orange-300 border-orange-700',
}
const DB_LABEL = { postgres: 'PG', mssql: 'MS' }

export default function ConnectionManager({ selected, onSelect }) {
  const [conns, setConns]           = useState([])
  const [form, setForm]             = useState(EMPTY)
  const [showForm, setShowForm]     = useState(false)
  const [testing, setTesting]       = useState(null)
  const [testResults, setTestResults] = useState({})

  useEffect(() => { load() }, [])

  async function load() {
    setConns(await api.list())
  }

  function handleDbTypeChange(db_type) {
    const def = DB_TYPES.find(d => d.value === db_type)
    setForm(f => ({
      ...f,
      db_type,
      port:     def?.defaultPort ?? f.port,
      username: db_type === 'mssql' ? 'sa' : 'postgres',
    }))
  }

  async function handleAdd(e) {
    e.preventDefault()
    const conn = await api.add({ ...form, port: Number(form.port) })
    setConns(prev => [...prev, conn])
    setForm(EMPTY)
    setShowForm(false)
  }

  async function handleDelete(id) {
    await api.remove(id)
    setConns(prev => prev.filter(c => c.id !== id))
    if (selected?.id === id) onSelect(null)
  }

  async function handleTest(id) {
    setTesting(id)
    const result = await api.test(id)
    setTestResults(prev => ({ ...prev, [id]: result }))
    setTesting(null)
  }

  return (
    <div className="h-full flex flex-col p-4 gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Server size={18} /> Connections
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 text-sm px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-md transition"
        >
          <Plus size={14} /> New
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="bg-gray-800 rounded-lg p-4 flex flex-col gap-3 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-300">New Connection</h3>

          {/* DB Type selector */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-400">Database Type</label>
            <div className="flex gap-2">
              {DB_TYPES.map(dt => (
                <button
                  key={dt.value}
                  type="button"
                  onClick={() => handleDbTypeChange(dt.value)}
                  className={`flex-1 py-1.5 rounded text-sm border transition ${
                    form.db_type === dt.value
                      ? dt.value === 'postgres'
                        ? 'bg-blue-700 border-blue-500 text-white'
                        : 'bg-orange-700 border-orange-500 text-white'
                      : 'bg-gray-900 border-gray-600 text-gray-400 hover:border-gray-400'
                  }`}
                >
                  {dt.label}
                </button>
              ))}
            </div>
          </div>

          {[
            ['name',     'Connection Name', 'text'],
            ['host',     'Host',            'text'],
            ['port',     'Port',            'number'],
            ['database', 'Database',        'text'],
            ['username', 'Username',        'text'],
            ['password', 'Password',        'password'],
          ].map(([field, label, type]) => (
            <div key={field} className="flex flex-col gap-1">
              <label className="text-xs text-gray-400">{label}</label>
              <input
                type={type}
                value={form[field]}
                onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))}
                required
                className="bg-gray-900 border border-gray-600 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          ))}

          {form.db_type === 'mssql' && (
            <p className="text-xs text-yellow-500/80 bg-yellow-950/30 border border-yellow-800/40 rounded p-2">
              Requires ODBC Driver 17 or 18 for SQL Server installed on this machine.
            </p>
          )}

          <div className="flex gap-2 mt-1">
            <button type="submit" className="flex-1 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm font-medium transition">
              Save
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="flex-1 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm transition">
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="flex flex-col gap-2 overflow-y-auto">
        {conns.length === 0 && (
          <p className="text-sm text-gray-500 text-center mt-8">No connections yet. Add one above.</p>
        )}
        {conns.map(conn => (
          <div
            key={conn.id}
            onClick={() => onSelect(conn)}
            className={`group rounded-lg p-3 cursor-pointer border transition ${
              selected?.id === conn.id
                ? 'border-blue-500 bg-blue-950/40'
                : 'border-gray-700 bg-gray-800/60 hover:border-gray-500'
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <span className={`text-xs font-mono px-1.5 py-0.5 rounded border shrink-0 ${DB_BADGE[conn.db_type] || DB_BADGE.postgres}`}>
                  {DB_LABEL[conn.db_type] || conn.db_type}
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white truncate">{conn.name}</p>
                  <p className="text-xs text-gray-400 font-mono truncate">
                    {conn.username}@{conn.host}:{conn.port}/{conn.database}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition shrink-0">
                <button
                  onClick={e => { e.stopPropagation(); handleTest(conn.id) }}
                  className="p-1 hover:text-blue-400 transition"
                  title="Test connection"
                >
                  {testing === conn.id
                    ? <Loader2 size={14} className="animate-spin" />
                    : testResults[conn.id]?.success === true  ? <CheckCircle size={14} className="text-green-400" />
                    : testResults[conn.id]?.success === false ? <XCircle size={14} className="text-red-400" />
                    : <CheckCircle size={14} />
                  }
                </button>
                <button
                  onClick={e => { e.stopPropagation(); handleDelete(conn.id) }}
                  className="p-1 hover:text-red-400 transition"
                  title="Delete"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
            {testResults[conn.id]?.error && (
              <p className="text-xs text-red-400 mt-1">{testResults[conn.id].error}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
