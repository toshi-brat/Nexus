import { useState, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Zap, TrendingUp, BarChart2, Brain, GitMerge,
  Play, PlayCircle, Plus, ChevronDown, ChevronUp,
  Clock, Target, ShieldAlert, Percent, AlertCircle,
  CheckCircle2, Loader2, Info,
} from 'lucide-react'
import { strategyApi, tradesApi } from '../lib/api'
import { fmt } from '../lib/utils'

// ─── Types ────────────────────────────────────────────────────────────────────
interface Signal {
  symbol: string
  strategy: string
  action: string
  instrument: string
  entry: number
  target: number
  stop_loss: number
  confidence: number
  kelly_pct: number
  qty: number
  capital_allocated: number
  rationale: string
  legs?: any[]
  scanned_at: string
  is_index: boolean
}

interface StrategyState {
  loading: boolean
  signals: Signal[]
  error: string | null
  lastRun: string | null
  expanded: boolean
}

// ─── Strategy Definitions ──────────────────────────────────────────────────────
const STRATEGIES = [
  {
    id: 'oi_gravity',
    name: 'OI Gravity',
    subtitle: 'Iron Condor',
    filter: 'OI Gravity',
    icon: GitMerge,
    color: 'text-[var(--color-gold)]',
    bg: 'bg-[var(--color-gold-highlight)]',
    border: 'border-[var(--color-gold)]/30',
    badge: 'INDEX ONLY',
    badgeColor: 'bg-[var(--color-gold-highlight)] text-[var(--color-gold)]',
    description: 'Detects neutral PCR + max pain zones on NIFTY/BANKNIFTY to sell Iron Condors.',
    universe: 'NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY',
    winRate: '65%',
  },
  {
    id: 'pcr_fade',
    name: 'PCR Momentum Fade',
    subtitle: 'Contrarian',
    filter: 'PCR',
    icon: BarChart2,
    color: 'text-[var(--color-blue)]',
    bg: 'bg-[var(--color-blue-highlight)]',
    border: 'border-[var(--color-blue)]/30',
    badge: 'INDEX ONLY',
    badgeColor: 'bg-[var(--color-blue-highlight)] text-[var(--color-blue)]',
    description: 'Fades extreme PCR readings at Bollinger Band extremes. Buys CE/PE on overextended moves.',
    universe: 'NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY',
    winRate: '55%',
  },
  {
    id: 'vol_breakout',
    name: 'Volatility Breakout',
    subtitle: 'Momentum',
    filter: 'Vol Breakout',
    icon: Zap,
    color: 'text-[var(--color-success)]',
    bg: 'bg-[var(--color-success-highlight)]',
    border: 'border-[var(--color-success)]/30',
    badge: 'ALL F&O STOCKS',
    badgeColor: 'bg-[var(--color-success-highlight)] text-[var(--color-success)]',
    description: 'Detects ATR compression + volume surge above recent highs. 1:3 R/R CE breakout.',
    universe: '185 NSE F&O symbols',
    winRate: '45%',
  },
  {
    id: 'sentiment',
    name: 'Sentiment Convergence',
    subtitle: 'NLP + Price',
    filter: 'Sentiment',
    icon: Brain,
    color: 'text-[var(--color-purple)]',
    bg: 'bg-[var(--color-purple-highlight)]',
    border: 'border-[var(--color-purple)]/30',
    badge: 'ALL F&O STOCKS',
    badgeColor: 'bg-[var(--color-purple-highlight)] text-[var(--color-purple)]',
    description: 'Combines NLP news sentiment score with price > 50 EMA for high-conviction CE buys.',
    universe: '185 NSE F&O symbols',
    winRate: '60%',
  },
  {
    id: 'stat_arb',
    name: 'Renaissance Stat-Arb',
    subtitle: 'Z-Score',
    filter: 'Stat-Arb',
    icon: TrendingUp,
    color: 'text-[var(--color-primary)]',
    bg: 'bg-[var(--color-primary-highlight)]',
    border: 'border-[var(--color-primary)]/30',
    badge: 'ALL F&O STOCKS',
    badgeColor: 'bg-[var(--color-primary-highlight)] text-[var(--color-primary)]',
    description: 'Detects Z-Score > 2 divergence between a stock and its correlated asset. Mean-reversion entry.',
    universe: '185 NSE F&O symbols',
    winRate: '51%',
  },
]

const INITIAL_STATE: StrategyState = {
  loading: false,
  signals: [],
  error: null,
  lastRun: null,
  expanded: true,
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
const rr = (entry: number, target: number, sl: number) => {
  const reward = Math.abs(target - entry)
  const risk = Math.abs(entry - sl)
  return risk > 0 ? (reward / risk).toFixed(1) : '—'
}

const timeAgo = (iso: string) => {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60)  return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

// ─── Signal Row ───────────────────────────────────────────────────────────────
function SignalRow({
  signal,
  onAddTrade,
  adding,
}: {
  signal: Signal
  onAddTrade: (s: Signal) => void
  adding: boolean
}) {
  const rrRatio = rr(signal.entry, signal.target, signal.stop_loss)
  const isLong = signal.action === 'BUY'

  return (
    <div className="grid grid-cols-[2fr_1fr_1fr_1fr_0.7fr_0.7fr_auto] gap-2 items-center px-4 py-2.5 border-b border-border last:border-0 hover:bg-[var(--color-surface-offset)] transition-colors text-xs">
      {/* Symbol + Instrument */}
      <div className="flex items-center gap-2">
        <span
          className={`shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded ${
            isLong
              ? 'bg-[var(--color-success-highlight)] text-[var(--color-success)]'
              : 'bg-[var(--color-error-highlight)] text-[var(--color-error)]'
          }`}
        >
          {signal.action}
        </span>
        <div>
          <div className="font-semibold text-[var(--color-text)] font-mono">{signal.symbol}</div>
          <div className="text-[var(--color-text-muted)] text-[10px]">{signal.instrument}</div>
        </div>
      </div>

      {/* Entry */}
      <div className="font-mono text-[var(--color-text)]">
        <div className="text-[10px] text-[var(--color-text-muted)] mb-0.5">Entry</div>
        {fmt.inr(signal.entry)}
      </div>

      {/* Target */}
      <div className="font-mono text-[var(--color-success)]">
        <div className="text-[10px] text-[var(--color-text-muted)] mb-0.5">Target</div>
        {fmt.inr(signal.target)}
      </div>

      {/* Stop Loss */}
      <div className="font-mono text-[var(--color-error)]">
        <div className="text-[10px] text-[var(--color-text-muted)] mb-0.5">SL</div>
        {fmt.inr(signal.stop_loss)}
      </div>

      {/* Confidence + R:R */}
      <div className="text-center">
        <div className="text-[10px] text-[var(--color-text-muted)] mb-0.5">Conf</div>
        <span
          className={`font-bold ${
            signal.confidence >= 80
              ? 'text-[var(--color-success)]'
              : signal.confidence >= 65
              ? 'text-[var(--color-gold)]'
              : 'text-[var(--color-text-muted)]'
          }`}
        >
          {signal.confidence}%
        </span>
      </div>

      {/* Kelly + R:R */}
      <div className="text-center">
        <div className="text-[10px] text-[var(--color-text-muted)] mb-0.5">R:R</div>
        <span className="font-mono font-medium">{rrRatio}x</span>
      </div>

      {/* Add to Paper Trade */}
      <button
        onClick={() => onAddTrade(signal)}
        disabled={adding}
        className="flex items-center gap-1 px-2.5 py-1.5 rounded text-[11px] font-medium bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50 transition-colors whitespace-nowrap"
      >
        {adding ? <Loader2 size={11} className="animate-spin" /> : <Plus size={11} />}
        Paper
      </button>
    </div>
  )
}

// ─── Strategy Card ─────────────────────────────────────────────────────────────
function StrategyCard({
  strategy,
  state,
  onRun,
  capital,
  timeframe,
}: {
  strategy: typeof STRATEGIES[0]
  state: StrategyState
  onRun: (filter: string) => void
  capital: number
  timeframe: string
}) {
  const [addingId, setAddingId] = useState<string | null>(null)
  const qc = useQueryClient()

  const addMutation = useMutation({
    mutationFn: (signal: Signal) =>
      tradesApi.addTrade({
        symbol: signal.symbol,
        trade_type: signal.action,
        instrument: signal.instrument,
        qty: signal.qty,
        entry_price: signal.entry,
        stop_loss: signal.stop_loss,
        target: signal.target,
        setup: signal.strategy,
        notes: `[STRATEGY SCANNER]\n${signal.rationale}`,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['trades'] })
      qc.invalidateQueries({ queryKey: ['trade-stats'] })
    },
  })

  const handleAddTrade = useCallback(
    async (signal: Signal) => {
      const key = `${signal.symbol}-${signal.strategy}-${signal.entry}`
      setAddingId(key)
      try {
        await addMutation.mutateAsync(signal)
      } finally {
        setAddingId(null)
      }
    },
    [addMutation]
  )

  const Icon = strategy.icon

  return (
    <div className={`rounded-xl border ${strategy.border} bg-[var(--color-surface)] overflow-hidden`}>
      {/* Card Header */}
      <div className="px-5 pt-5 pb-4 flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${strategy.bg}`}>
            <Icon size={18} className={strategy.color} />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-[var(--color-text)] text-sm">{strategy.name}</h3>
              <span className="text-xs text-[var(--color-text-muted)]">· {strategy.subtitle}</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${strategy.badgeColor}`}>
                {strategy.badge}
              </span>
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mt-1 leading-relaxed max-w-md">
              {strategy.description}
            </p>
          </div>
        </div>

        {/* Meta */}
        <div className="text-right shrink-0 space-y-1">
          <div className="text-xs text-[var(--color-text-muted)]">
            Win rate ~{strategy.winRate}
          </div>
          {state.lastRun && (
            <div className="flex items-center gap-1 text-[10px] text-[var(--color-text-faint)] justify-end">
              <Clock size={10} />
              {timeAgo(state.lastRun)}
            </div>
          )}
        </div>
      </div>

      {/* Stats bar */}
      <div className="px-5 pb-4 flex items-center gap-6">
        <div className="text-xs text-[var(--color-text-muted)]">
          Universe: <span className="text-[var(--color-text)] font-medium">{strategy.universe}</span>
        </div>
        {state.signals.length > 0 && (
          <div className="text-xs">
            <span className="text-[var(--color-success)] font-semibold">{state.signals.length}</span>
            <span className="text-[var(--color-text-muted)]"> signal{state.signals.length !== 1 ? 's' : ''} found</span>
          </div>
        )}
        {state.error && (
          <div className="flex items-center gap-1 text-xs text-[var(--color-error)]">
            <AlertCircle size={12} />
            {state.error}
          </div>
        )}
      </div>

      {/* Action bar */}
      <div className="px-5 pb-4 flex items-center gap-3">
        <button
          onClick={() => onRun(strategy.filter)}
          disabled={state.loading}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            state.loading
              ? 'bg-[var(--color-surface-offset)] text-[var(--color-text-muted)] cursor-not-allowed'
              : `${strategy.bg} ${strategy.color} hover:opacity-80`
          }`}
        >
          {state.loading ? (
            <><Loader2 size={14} className="animate-spin" /> Scanning {strategy.universe.split(',').length > 1 ? '185' : '4'} symbols…</>
          ) : (
            <><Play size={14} /> Run Strategy</>
          )}
        </button>

        {state.signals.length > 0 && (
          <button
            onClick={() =>
              // toggle expand inline
              state.expanded
                ? document.getElementById(`results-${strategy.id}`)?.classList.add('hidden')
                : document.getElementById(`results-${strategy.id}`)?.classList.remove('hidden')
            }
            className="flex items-center gap-1 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
          >
            {state.expanded ? <><ChevronUp size={14} /> Hide results</> : <><ChevronDown size={14} /> Show results</>}
          </button>
        )}
      </div>

      {/* Results Table */}
      {state.signals.length > 0 && (
        <div id={`results-${strategy.id}`} className="border-t border-border">
          {/* Table header */}
          <div className="grid grid-cols-[2fr_1fr_1fr_1fr_0.7fr_0.7fr_auto] gap-2 px-4 py-2 bg-[var(--color-surface-offset)] text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            <div>Symbol</div>
            <div>Entry</div>
            <div>Target</div>
            <div>Stop Loss</div>
            <div className="text-center">Conf</div>
            <div className="text-center">R:R</div>
            <div></div>
          </div>
          {state.signals.map((sig, i) => (
            <SignalRow
              key={`${sig.symbol}-${i}`}
              signal={sig}
              onAddTrade={handleAddTrade}
              adding={addingId === `${sig.symbol}-${sig.strategy}-${sig.entry}`}
            />
          ))}

          {/* Rationale tooltip for first result */}
          <div className="px-4 py-2.5 bg-[var(--color-surface-offset)] flex items-start gap-2 text-[11px] text-[var(--color-text-muted)]">
            <Info size={12} className="mt-0.5 shrink-0" />
            <span className="leading-relaxed">{state.signals[0]?.rationale}</span>
          </div>
        </div>
      )}

      {/* Empty state after run */}
      {!state.loading && state.lastRun && state.signals.length === 0 && !state.error && (
        <div className="border-t border-border px-5 py-6 flex flex-col items-center gap-2 text-[var(--color-text-muted)]">
          <CheckCircle2 size={20} className="text-[var(--color-text-faint)]" />
          <p className="text-sm">No signals matching conditions right now.</p>
          <p className="text-xs text-[var(--color-text-faint)]">Market may be in a quiet phase. Try a different timeframe.</p>
        </div>
      )}
    </div>
  )
}

// ─── Main Page ─────────────────────────────────────────────────────────────────
export default function Strategy() {
  const [states, setStates] = useState<Record<string, StrategyState>>(
    Object.fromEntries(STRATEGIES.map((s) => [s.id, { ...INITIAL_STATE }]))
  )

  const [capital, setCapital] = useState(100000)
  const [timeframe, setTimeframe] = useState('15m')
  const [runningAll, setRunningAll] = useState(false)

  const updateState = (id: string, patch: Partial<StrategyState>) =>
    setStates((prev) => ({ ...prev, [id]: { ...prev[id], ...patch } }))

  const runStrategy = useCallback(
    async (filter: string) => {
      const strategy = STRATEGIES.find((s) => s.filter === filter)!
      updateState(strategy.id, { loading: true, error: null, signals: [] })

      try {
        const res = await strategyApi.runScan({
          timeframe,
          days: 10,
          capital,
          strategy: filter,
          save: true,
        })
        const signals: Signal[] = res.signals ?? []
        updateState(strategy.id, {
          loading: false,
          signals,
          lastRun: new Date().toISOString(),
          expanded: true,
        })
      } catch (err: any) {
        updateState(strategy.id, {
          loading: false,
          error: err?.message ?? 'Scan failed',
          lastRun: new Date().toISOString(),
        })
      }
    },
    [capital, timeframe]
  )

  const runAll = useCallback(async () => {
    setRunningAll(true)
    await Promise.allSettled(STRATEGIES.map((s) => runStrategy(s.filter)))
    setRunningAll(false)
  }, [runStrategy])

  const totalSignals = Object.values(states).reduce((sum, s) => sum + s.signals.length, 0)
  const anyLoading = Object.values(states).some((s) => s.loading)

  return (
    <div className="space-y-6">
      {/* ── Page Header ── */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Target className="text-[var(--color-primary)]" size={24} />
            <h1 className="text-2xl font-bold tracking-tight">Strategy Scanner</h1>
          </div>
          <p className="text-sm text-[var(--color-text-muted)]">
            Run any strategy manually across{' '}
            <span className="text-[var(--color-text)] font-medium">185 NSE F&O symbols</span>.
            No automated fetch — runs only when you click.
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 bg-[var(--color-surface)] border border-border rounded-lg px-3 py-2">
            <span className="text-xs text-[var(--color-text-muted)]">Capital</span>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              className="w-28 text-xs font-mono bg-transparent text-[var(--color-text)] outline-none"
              step={10000}
              min={10000}
            />
          </div>

          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="bg-[var(--color-surface)] border border-border text-xs rounded-lg px-3 py-2 text-[var(--color-text)] outline-none"
          >
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="30m">30m</option>
            <option value="1h">1h</option>
            <option value="1d">1d</option>
          </select>

          <button
            onClick={runAll}
            disabled={anyLoading || runningAll}
            className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50 transition-colors"
          >
            {runningAll ? (
              <><Loader2 size={15} className="animate-spin" /> Running all…</>
            ) : (
              <><PlayCircle size={15} /> Run All 5</>
            )}
          </button>
        </div>
      </div>

      {/* ── Signal count banner ── */}
      {totalSignals > 0 && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-[var(--color-primary-highlight)] border border-[var(--color-primary)]/20 text-sm">
          <CheckCircle2 size={16} className="text-[var(--color-primary)]" />
          <span className="text-[var(--color-text)]">
            <span className="font-bold text-[var(--color-primary)]">{totalSignals}</span> signal
            {totalSignals !== 1 ? 's' : ''} found across{' '}
            {Object.values(states).filter((s) => s.signals.length > 0).length} strateg
            {Object.values(states).filter((s) => s.signals.length > 0).length === 1 ? 'y' : 'ies'}.
            Click <span className="font-semibold">Paper</span> on any row to add to your trade journal.
          </span>
        </div>
      )}

      {/* ── Strategy Cards ── */}
      <div className="space-y-4">
        {STRATEGIES.map((strategy) => (
          <StrategyCard
            key={strategy.id}
            strategy={strategy}
            state={states[strategy.id]}
            onRun={runStrategy}
            capital={capital}
            timeframe={timeframe}
          />
        ))}
      </div>

      {/* ── Legend ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-[var(--color-text-muted)]">
        <div className="flex items-center gap-2 p-3 rounded-lg bg-[var(--color-surface)] border border-border">
          <ShieldAlert size={14} className="text-[var(--color-primary)] shrink-0" />
          <span><span className="font-medium text-[var(--color-text)]">Conf</span> — strategy confidence score (0–100%)</span>
        </div>
        <div className="flex items-center gap-2 p-3 rounded-lg bg-[var(--color-surface)] border border-border">
          <Percent size={14} className="text-[var(--color-gold)] shrink-0" />
          <span><span className="font-medium text-[var(--color-text)]">R:R</span> — reward-to-risk ratio of the setup</span>
        </div>
        <div className="flex items-center gap-2 p-3 rounded-lg bg-[var(--color-surface)] border border-border">
          <Target size={14} className="text-[var(--color-success)] shrink-0" />
          <span><span className="font-medium text-[var(--color-text)]">Kelly</span> — Half-Kelly position sizing % of capital</span>
        </div>
        <div className="flex items-center gap-2 p-3 rounded-lg bg-[var(--color-surface)] border border-border">
          <Plus size={14} className="text-[var(--color-purple)] shrink-0" />
          <span><span className="font-medium text-[var(--color-text)]">Paper</span> — adds to Trade Journal for tracking</span>
        </div>
      </div>
    </div>
  )
}
