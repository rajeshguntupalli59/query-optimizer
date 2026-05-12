import { useState } from 'react'
import { Database, KeyRound, Loader2 } from 'lucide-react'

export default function Activate({ onActivated }) {
  const [key, setKey]       = useState('')
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch('/api/license/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: key.trim() }),
      })
      const data = await res.json()
      if (data.activated) {
        onActivated()
      } else {
        setError(data.error || 'Invalid license key.')
      }
    } catch {
      setError('Could not reach the server. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen bg-gray-950 flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center mx-auto mb-5 shadow-xl shadow-blue-900/40">
            <Database size={26} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">QueryOptimizer</h1>
          <p className="text-sm text-gray-400">Enter your license key to activate this installation.</p>
        </div>

        <form onSubmit={submit} className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">License Key</label>
            <div className="relative">
              <KeyRound size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
              <input
                type="text"
                value={key}
                onChange={e => setKey(e.target.value.toUpperCase())}
                placeholder="QO-XXXX-XXXX-XXXX-XXXX-XXXX"
                spellCheck={false}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-4 py-2.5 text-sm font-mono text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition"
              />
            </div>
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-950/40 border border-red-900/40 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            type="submit"
            disabled={!key.trim() || loading}
            className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-lg text-sm transition"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <KeyRound size={14} />}
            {loading ? 'Activating…' : 'Activate'}
          </button>
        </form>

        <p className="text-center text-xs text-gray-700 mt-5">
          License key is included in your purchase receipt.<br />
          Questions? Email <span className="text-gray-500">support@queryoptimizer.dev</span>
        </p>
      </div>
    </div>
  )
}
