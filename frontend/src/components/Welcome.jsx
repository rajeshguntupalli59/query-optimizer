import { Zap, Search, Clock, Wand2, ArrowRight, CheckCircle } from 'lucide-react'

const FEATURES = [
  {
    icon: Zap,
    color: 'from-blue-600 to-blue-400',
    glow: 'shadow-blue-500/20',
    border: 'border-blue-700/40',
    label: 'EXPLAIN Visualizer',
    desc: 'Run EXPLAIN and EXPLAIN ANALYZE against your live database. Interactive plan tree with cost breakdown, row estimate warnings, and seq scan detection.',
    bullets: ['Collapsible node tree', 'Seq scan & join warnings', 'Row estimate drift alerts'],
    tab: 'explain',
  },
  {
    icon: Search,
    color: 'from-purple-600 to-purple-400',
    glow: 'shadow-purple-500/20',
    border: 'border-purple-700/40',
    label: 'Index Advisor',
    desc: 'Analyze your query against live catalog data to surface missing indexes, unindexed FK columns, and WHERE / ORDER BY gaps.',
    bullets: ['Live catalog analysis', 'FK index detection', 'Copy-ready CREATE INDEX DDL'],
    tab: 'indexes',
  },
  {
    icon: Clock,
    color: 'from-orange-600 to-orange-400',
    glow: 'shadow-orange-500/20',
    border: 'border-orange-700/40',
    label: 'Slow Query Dashboard',
    desc: 'Surface your worst-performing queries from pg_stat_statements (PostgreSQL) or sys.dm_exec_query_stats (SQL Server) with timing histograms.',
    bullets: ['Mean / min / max timing', 'Cache hit rate', 'Full query text on demand'],
    tab: 'slow',
  },
  {
    icon: Wand2,
    color: 'from-emerald-600 to-emerald-400',
    glow: 'shadow-emerald-500/20',
    border: 'border-emerald-700/40',
    label: 'Query Rewriter',
    desc: 'Paste any SQL and get instant rule-based analysis. Catches anti-patterns before they hit production — no database connection needed.',
    bullets: ['SELECT *, NOT IN, OR anti-patterns', 'Leading wildcard detection', 'OFFSET pagination warnings'],
    tab: 'rewrite',
  },
]

const STEPS = [
  { n: '1', text: 'Click New in the sidebar and add a PostgreSQL or SQL Server connection' },
  { n: '2', text: 'Hit the checkmark to verify connectivity' },
  { n: '3', text: 'Pick a tab above and start analyzing queries' },
]

export default function Welcome({ onTabSelect }) {
  return (
    <div className="max-w-5xl mx-auto py-10 px-4 flex flex-col gap-10">

      {/* Hero */}
      <div className="text-center flex flex-col items-center gap-3">
        <div className="inline-flex items-center gap-2 bg-blue-950/60 border border-blue-800/50 rounded-full px-4 py-1.5 text-xs text-blue-300 font-medium mb-1">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 inline-block animate-pulse" />
          Supports PostgreSQL &amp; Microsoft SQL Server
        </div>
        <h1 className="text-3xl font-bold text-white tracking-tight">
          SQL Query Optimizer
        </h1>
        <p className="text-gray-400 max-w-xl text-sm leading-relaxed">
          A DBA workbench for diagnosing slow queries, finding missing indexes, visualizing
          execution plans, and catching SQL anti-patterns — all from one interface.
        </p>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {FEATURES.map(f => {
          const Icon = f.icon
          return (
            <div
              key={f.tab}
              onClick={() => onTabSelect(f.tab)}
              className={`group relative rounded-xl border ${f.border} bg-gray-900/80 p-5 flex flex-col gap-3 cursor-pointer hover:bg-gray-800/80 transition-all duration-200 shadow-lg ${f.glow} hover:shadow-xl`}
            >
              {/* Icon + label */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${f.color} flex items-center justify-center shadow-md`}>
                    <Icon size={16} className="text-white" />
                  </div>
                  <span className="font-semibold text-white text-sm">{f.label}</span>
                </div>
                <ArrowRight size={14} className="text-gray-600 group-hover:text-gray-300 group-hover:translate-x-0.5 transition-all" />
              </div>

              {/* Description */}
              <p className="text-xs text-gray-400 leading-relaxed">{f.desc}</p>

              {/* Bullets */}
              <ul className="flex flex-col gap-1">
                {f.bullets.map(b => (
                  <li key={b} className="flex items-center gap-2 text-xs text-gray-500">
                    <CheckCircle size={11} className="text-gray-600 shrink-0" />
                    {b}
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
      </div>

      {/* Getting started */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <h2 className="text-sm font-semibold text-gray-300 mb-4">Getting started</h2>
        <div className="flex flex-col sm:flex-row gap-4">
          {STEPS.map(s => (
            <div key={s.n} className="flex items-start gap-3 flex-1">
              <span className="w-6 h-6 rounded-full bg-gray-800 border border-gray-700 text-xs text-gray-400 font-mono font-bold flex items-center justify-center shrink-0 mt-0.5">
                {s.n}
              </span>
              <p className="text-xs text-gray-400 leading-relaxed">{s.text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* DB support badges */}
      <div className="flex items-center justify-center gap-3 flex-wrap">
        {[
          ['PG', 'PostgreSQL 12+', 'bg-blue-900/40 border-blue-700/50 text-blue-300'],
          ['MS', 'SQL Server 2016+', 'bg-orange-900/40 border-orange-700/50 text-orange-300'],
          ['EXPLAIN', 'Execution Plans', 'bg-gray-800 border-gray-700 text-gray-400'],
          ['DMV', 'Dynamic Mgmt Views', 'bg-gray-800 border-gray-700 text-gray-400'],
          ['stat_statements', 'pg_stat_statements', 'bg-gray-800 border-gray-700 text-gray-400'],
        ].map(([short, label, cls]) => (
          <span key={short} className={`text-xs px-3 py-1 rounded-full border font-mono ${cls}`}>
            {label}
          </span>
        ))}
      </div>

    </div>
  )
}
