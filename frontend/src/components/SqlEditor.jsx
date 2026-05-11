import { useState } from 'react'
import Editor from '@monaco-editor/react'
import { Play, Loader2, AlertTriangle } from 'lucide-react'

export default function SqlEditor({ value, onChange, onRun, loading, error, label = 'Run Query' }) {
  return (
    <div className="flex flex-col gap-2 h-full">
      <div className="rounded-lg overflow-hidden border border-gray-700 flex-1 min-h-0">
        <Editor
          height="100%"
          defaultLanguage="sql"
          value={value}
          onChange={onChange}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: 'JetBrains Mono, Fira Code, monospace',
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            padding: { top: 12 },
            tabSize: 2,
          }}
        />
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onRun}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 rounded-md text-sm font-medium transition"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          {label}
        </button>
        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <AlertTriangle size={14} />
            <span className="truncate max-w-md">{error}</span>
          </div>
        )}
      </div>
    </div>
  )
}
