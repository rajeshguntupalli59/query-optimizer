import { useState, useEffect } from 'react'
import { aiAssistant } from '../api/client'
import { Settings2, CheckCircle, AlertTriangle, Loader2, ExternalLink, Sparkles } from 'lucide-react'

const PROVIDERS = [
  { value: 'openai',    label: 'OpenAI',          placeholder: 'https://api.openai.com/v1/chat/completions',    models: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
  { value: 'anthropic', label: 'Anthropic',        placeholder: 'https://api.anthropic.com/v1/messages',         models: ['claude-opus-4-7', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'] },
  { value: 'ollama',    label: 'Ollama (local)',   placeholder: 'http://localhost:11434/api/generate',            models: ['llama3', 'mistral', 'codellama', 'deepseek-coder'] },
  { value: 'generic',   label: 'Generic / Azure', placeholder: 'https://your-endpoint/v1/chat/completions',     models: [] },
]

export default function Settings() {
  const [cfg, setCfg]         = useState({ endpoint: '', api_key: '', model: '', provider: 'openai', enabled: false })
  const [saved, setSaved]     = useState(false)
  const [saving, setSaving]   = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')

  useEffect(() => {
    aiAssistant.getConfig().then(data => { setCfg(data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const provider = PROVIDERS.find(p => p.value === cfg.provider) || PROVIDERS[0]

  function handleProviderChange(val) {
    const p = PROVIDERS.find(x => x.value === val)
    setCfg(c => ({ ...c, provider: val, endpoint: p?.placeholder || '', model: p?.models[0] || '' }))
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true); setError('')
    try {
      await aiAssistant.saveConfig({ endpoint: cfg.endpoint, api_key: cfg.api_key, model: cfg.model, provider: cfg.provider })
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
      const fresh = await aiAssistant.getConfig()
      setCfg(fresh)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="flex items-center justify-center h-40 text-gray-500 text-sm">Loading settings…</div>

  return (
    <div className="max-w-2xl flex flex-col gap-8">

      {/* AI Integration */}
      <section className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-purple-400" />
          <h3 className="text-sm font-semibold text-gray-200">AI Integration</h3>
          <span className={`ml-auto text-xs px-2 py-0.5 rounded-full border ${cfg.enabled ? 'border-emerald-700 bg-emerald-950/40 text-emerald-400' : 'border-gray-700 bg-gray-800 text-gray-500'}`}>
            {cfg.enabled ? 'Configured' : 'Not configured'}
          </span>
        </div>

        <p className="text-xs text-gray-500 leading-relaxed">
          Connect your own LLM to power AI query analysis. Supports OpenAI, Anthropic, self-hosted
          Ollama, Azure OpenAI, or any OpenAI-compatible endpoint.
          <br />This setting is stored locally on your server — your API key never leaves your infrastructure.
        </p>

        <form onSubmit={handleSave} className="flex flex-col gap-4 bg-gray-900/60 border border-gray-800 rounded-xl p-5">

          {/* Provider */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-gray-400 font-medium">Provider</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {PROVIDERS.map(p => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => handleProviderChange(p.value)}
                  className={`py-2 px-3 rounded-lg text-xs border transition ${
                    cfg.provider === p.value
                      ? 'bg-blue-700/60 border-blue-500 text-blue-200'
                      : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Endpoint */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-gray-400 font-medium">API Endpoint</label>
            <input
              value={cfg.endpoint}
              onChange={e => setCfg(c => ({ ...c, endpoint: e.target.value }))}
              placeholder={provider.placeholder}
              className="bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono placeholder-gray-700 focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          {/* API Key */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-gray-400 font-medium">
              API Key
              {cfg.provider === 'ollama' && <span className="text-gray-600 ml-1">(not required for local Ollama)</span>}
            </label>
            <input
              type="password"
              value={cfg.api_key}
              onChange={e => setCfg(c => ({ ...c, api_key: e.target.value }))}
              placeholder={cfg.provider === 'ollama' ? 'Leave blank' : 'sk-…'}
              className="bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono placeholder-gray-700 focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          {/* Model */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-gray-400 font-medium">Model</label>
            {provider.models.length > 0 ? (
              <select
                value={cfg.model}
                onChange={e => setCfg(c => ({ ...c, model: e.target.value }))}
                className="bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition"
              >
                {provider.models.map(m => <option key={m} value={m}>{m}</option>)}
                <option value="__custom__">Custom…</option>
              </select>
            ) : (
              <input
                value={cfg.model}
                onChange={e => setCfg(c => ({ ...c, model: e.target.value }))}
                placeholder="model name"
                className="bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono placeholder-gray-700 focus:outline-none focus:border-blue-500 transition"
              />
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-400 text-xs bg-red-950/30 border border-red-800/40 rounded-lg px-3 py-2">
              <AlertTriangle size={12} /> {error}
            </div>
          )}

          <div className="flex items-center gap-3 pt-1">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition"
            >
              {saving ? <Loader2 size={13} className="animate-spin" /> : null}
              Save Settings
            </button>
            {saved && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-400">
                <CheckCircle size={13} /> Saved
              </span>
            )}
          </div>
        </form>
      </section>

      {/* About */}
      <section className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Settings2 size={15} className="text-gray-500" />
          <h3 className="text-sm font-semibold text-gray-200">About</h3>
        </div>
        <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5 flex flex-col gap-3 text-xs text-gray-500">
          <div className="grid grid-cols-2 gap-y-2">
            {[
              ['Product',  'QueryOptimizer'],
              ['Version',  '1.0.0'],
              ['License',  'Commercial — Self-Hosted'],
              ['Support',  'Included with purchase'],
            ].map(([k, v]) => (
              <div key={k} className="contents">
                <span className="text-gray-600">{k}</span>
                <span className="text-gray-400">{v}</span>
              </div>
            ))}
          </div>
          <p className="pt-1 text-gray-600 leading-relaxed">
            This is a self-hosted, on-premise tool. All data — database connections, query history,
            and settings — stays within your own infrastructure. The vendor has no access to
            your environment after installation.
          </p>
        </div>
      </section>

    </div>
  )
}
