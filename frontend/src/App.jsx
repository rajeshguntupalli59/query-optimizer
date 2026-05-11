import { useState } from 'react'
import ConnectionManager from './components/ConnectionManager'
import ExplainPlan from './components/ExplainPlan'
import IndexAdvisor from './components/IndexAdvisor'
import SlowQueries from './components/SlowQueries'
import QueryRewriter from './components/QueryRewriter'
import AiAssistant from './components/AiAssistant'
import Settings from './components/Settings'
import Welcome from './components/Welcome'
import {
  Database, Zap, Search, Clock, Wand2,
  ChevronLeft, ChevronRight, LayoutDashboard,
  Sparkles, Settings2,
} from 'lucide-react'

const TABS = [
  { id: 'explain',  label: 'EXPLAIN',       icon: Zap,        component: ExplainPlan,  needsConn: true  },
  { id: 'indexes',  label: 'Index Advisor',  icon: Search,     component: IndexAdvisor, needsConn: true  },
  { id: 'slow',     label: 'Slow Queries',   icon: Clock,      component: SlowQueries,  needsConn: true  },
  { id: 'rewrite',  label: 'Query Rewriter', icon: Wand2,      component: QueryRewriter,needsConn: false },
  { id: 'ai',       label: 'AI Assistant',   icon: Sparkles,   component: AiAssistant,  needsConn: false },
]

const DB_COLOR = { postgres: 'bg-blue-500', mssql: 'bg-orange-500' }
const DB_LABEL = { postgres: 'PostgreSQL',  mssql: 'SQL Server'    }

export default function App() {
  const [selectedConn, setSelectedConn] = useState(null)
  const [activeTab, setActiveTab]       = useState(null)
  const [sidebarOpen, setSidebarOpen]   = useState(true)

  const active = TABS.find(t => t.id === activeTab)
  const ActiveComponent = active?.component

  function selectTab(id) {
    if (id === 'settings') { setActiveTab('settings'); return }
    const tab = TABS.find(t => t.id === id)
    if (tab?.needsConn && !selectedConn) return
    setActiveTab(id)
  }

  function handleConnSelect(conn) {
    setSelectedConn(conn)
    if (conn && (!activeTab || (active?.needsConn && !selectedConn))) setActiveTab('explain')
    if (!conn && active?.needsConn) setActiveTab(null)
  }

  const showWelcome = !activeTab || (!selectedConn && active?.needsConn)
  const showSettings = activeTab === 'settings'

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-gray-950 text-gray-100">

      {/* ── Header ── */}
      <header className="h-14 shrink-0 flex items-center gap-3 px-5 border-b border-gray-800/80 bg-gray-900">
        <button onClick={() => setActiveTab(null)} className="flex items-center gap-2.5 group mr-1">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-md shadow-blue-900/40">
            <Database size={14} className="text-white" />
          </div>
          <div className="leading-none">
            <p className="text-sm font-bold text-white tracking-tight group-hover:text-blue-300 transition">QueryOptimizer</p>
            <p className="text-[10px] text-gray-500 font-medium">DBA Workbench</p>
          </div>
        </button>

        <div className="w-px h-6 bg-gray-800 mx-0.5" />

        {/* Nav */}
        <nav className="flex items-center gap-0.5">
          <button
            onClick={() => setActiveTab(null)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${showWelcome ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/60'}`}
          >
            <LayoutDashboard size={12} /> Overview
          </button>

          {TABS.map(tab => {
            const Icon = tab.icon
            const disabled  = tab.needsConn && !selectedConn
            const isActive  = activeTab === tab.id
            const isAiTab   = tab.id === 'ai'
            return (
              <button
                key={tab.id}
                onClick={() => selectTab(tab.id)}
                disabled={disabled}
                title={disabled ? 'Connect to a database first' : ''}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  isActive
                    ? isAiTab ? 'bg-purple-900/60 text-purple-200' : 'bg-gray-800 text-white'
                    : disabled
                      ? 'text-gray-700 cursor-not-allowed'
                      : isAiTab
                        ? 'text-purple-500 hover:text-purple-300 hover:bg-purple-900/30'
                        : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/60'
                }`}
              >
                <Icon size={12} /> {tab.label}
              </button>
            )
          })}
        </nav>

        <div className="flex-1" />

        {/* Connection pill */}
        {selectedConn ? (
          <div className="flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-full px-3 py-1.5">
            <span className={`w-2 h-2 rounded-full shrink-0 ${DB_COLOR[selectedConn.db_type] || 'bg-gray-400'}`} />
            <span className="text-xs text-gray-300 font-medium">{selectedConn.name}</span>
            <span className="text-gray-600 text-xs">·</span>
            <span className="text-xs text-gray-500">{DB_LABEL[selectedConn.db_type] || selectedConn.db_type}</span>
            <span className="text-gray-600 text-xs">·</span>
            <span className="text-xs font-mono text-gray-400">{selectedConn.database}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 bg-gray-800/40 border border-dashed border-gray-700 rounded-full px-3 py-1.5">
            <span className="w-2 h-2 rounded-full bg-gray-700 shrink-0" />
            <span className="text-xs text-gray-600">No connection</span>
          </div>
        )}

        {/* Settings button */}
        <button
          onClick={() => selectTab('settings')}
          className={`p-2 rounded-lg transition ${showSettings ? 'bg-gray-800 text-white' : 'text-gray-600 hover:text-gray-300 hover:bg-gray-800/60'}`}
          title="Settings"
        >
          <Settings2 size={15} />
        </button>
      </header>

      {/* ── Body ── */}
      <div className="flex flex-1 min-h-0">

        <aside className={`shrink-0 flex flex-col border-r border-gray-800/80 bg-gray-900/60 transition-all duration-200 ${sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'}`}>
          <ConnectionManager selected={selectedConn} onSelect={handleConnSelect} />
        </aside>

        <button
          onClick={() => setSidebarOpen(o => !o)}
          className="shrink-0 w-4 flex items-center justify-center border-r border-gray-800/80 text-gray-700 hover:text-gray-400 hover:bg-gray-800/40 transition"
        >
          {sidebarOpen ? <ChevronLeft size={11} /> : <ChevronRight size={11} />}
        </button>

        <main className="flex-1 min-w-0 overflow-y-auto">
          {showSettings ? (
            <div className="p-6 flex flex-col gap-4">
              <div className="flex items-center gap-2 pb-4 border-b border-gray-800/60">
                <Settings2 size={15} className="text-gray-400" />
                <h2 className="text-sm font-semibold text-gray-200">Settings</h2>
              </div>
              <Settings />
            </div>
          ) : showWelcome ? (
            <Welcome onTabSelect={selectTab} />
          ) : (
            <div className="p-6 h-full flex flex-col gap-4">
              <div className="shrink-0 flex items-center gap-3 pb-4 border-b border-gray-800/60">
                {active && (() => { const Icon = active.icon; return <Icon size={15} className="text-gray-400" /> })()}
                <h2 className="text-sm font-semibold text-gray-200">{active?.label}</h2>
                {active?.needsConn && selectedConn && (
                  <>
                    <span className="text-xs text-gray-700">on</span>
                    <span className="text-xs font-mono text-gray-500">{selectedConn.database}</span>
                  </>
                )}
              </div>
              {ActiveComponent && (
                <ActiveComponent
                  connectionId={selectedConn?.id}
                  dbType={selectedConn?.db_type}
                  onGoToSettings={() => selectTab('settings')}
                />
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
