import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { tradesApi } from '../lib/api'
import { fmt, colorPnl } from '../lib/utils'
import { BookOpen, Plus, Crosshair, Notebook, Trash2 } from 'lucide-react'

export default function PaperTrade() {
  const qc = useQueryClient()
  const { data: stats, isLoading: loadStats } = useQuery({ queryKey: ['trade-stats'], queryFn: tradesApi.getStats })
  const { data: trades, isLoading: loadTrades } = useQuery({ queryKey: ['trades'], queryFn: () => tradesApi.getTrades() })
  const deleteTradeMutation = useMutation({
    mutationFn: (tradeId: number) => tradesApi.deleteTrade(tradeId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['trades'] })
      qc.invalidateQueries({ queryKey: ['trade-stats'] })
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <BookOpen className="text-primary" size={24} />
          <h1 className="text-2xl font-bold tracking-tight">Trade Journal & Paper Trading</h1>
        </div>
        <button className="btn-primary flex items-center gap-2"><Plus size={16} /> New Trade</button>
      </div>

      {loadStats ? <div className="h-32 shimmer rounded w-full mb-6"></div> : (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="card p-4"><span className="label text-[0.65rem]">Win Rate</span><div className="text-xl font-bold num mt-1 text-primary">{stats?.win_rate}%</div></div>
          <div className="card p-4"><span className="label text-[0.65rem]">Total P&L</span><div className={`text-xl font-bold num mt-1 ${colorPnl(stats?.total_pnl)}`}>{fmt.inr(stats?.total_pnl)}</div></div>
          <div className="card p-4"><span className="label text-[0.65rem]">Total Trades</span><div className="text-xl font-bold num mt-1">{stats?.total}</div></div>
          <div className="card p-4"><span className="label text-[0.65rem]">Avg Winner</span><div className="text-xl font-bold num mt-1 text-gain">{fmt.inr(stats?.avg_win)}</div></div>
          <div className="card p-4"><span className="label text-[0.65rem]">Avg Loser</span><div className="text-xl font-bold num mt-1 text-loss">{fmt.inr(stats?.avg_loss)}</div></div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Trade History */}
        <div className="xl:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2"><Crosshair size={18} className="text-tx-m"/> Recent Executions</h2>
          <div className="card p-0 overflow-hidden">
            {loadTrades ? <div className="h-64 shimmer w-full"></div> : trades?.map((t: any) => (
              <div key={t.id} className="p-4 border-b border-border hover:bg-s2 transition-colors flex justify-between items-center group">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded flex flex-col items-center justify-center shrink-0 ${t.trade_type==='BUY'?'bg-gain/10 text-gain':'bg-loss/10 text-loss'}`}>
                    <span className="text-[0.6rem] font-bold">{t.trade_type}</span>
                    <span className="text-xs font-mono">{t.qty}</span>
                  </div>
                  <div>
                    <div className="font-semibold flex items-center gap-2">
                      {t.symbol} 
                      {t.instrument !== 'EQ' && <span className="text-xs px-1.5 py-0.5 bg-s3 rounded text-tx-m">{t.strike} {t.instrument}</span>}
                      {t.status === 'OPEN' && <span className="text-[0.6rem] uppercase bg-warn/20 text-warn px-2 py-0.5 rounded-full">Open</span>}
                    </div>
                    <div className="text-xs text-tx-f mt-1 flex gap-3 font-mono">
                      <span>In: {fmt.price(t.entry_price)}</span>
                      {t.exit_price && <span>Out: {fmt.price(t.exit_price)}</span>}
                      <span>{fmt.date(t.entry_time)}</span>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  {t.status === 'CLOSED' ? (
                    <>
                      <div className={`num font-bold text-lg ${colorPnl(t.pnl)}`}>{fmt.inr(t.pnl)}</div>
                      <div className={`num text-xs ${colorPnl(t.pnl_pct)}`}>{fmt.pct(t.pnl_pct)}</div>
                    </>
                  ) : (
                    <button className="btn-ghost text-xs py-1">Exit Position</button>
                  )}
                  <button
                    className="btn-ghost text-xs py-1 mt-2 text-loss hover:bg-loss/10"
                    onClick={() => deleteTradeMutation.mutate(t.id)}
                    disabled={deleteTradeMutation.isPending}
                    title="Delete trade entry"
                  >
                    <span className="inline-flex items-center gap-1">
                      <Trash2 size={12} />
                      Delete
                    </span>
                  </button>
                </div>
              </div>
            ))}
            {trades?.length === 0 && <div className="p-8 text-center text-tx-m">No trades recorded yet.</div>}
          </div>
        </div>

        {/* Daily Journal Context */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2"><Notebook size={18} className="text-blue"/> Daily Reflection</h2>
          <div className="card p-5 bg-gradient-to-b from-s2 to-bg border-t-2 border-t-primary h-[calc(100%-2.5rem)]">
            <div className="text-xs font-mono text-tx-m mb-4">{new Date().toLocaleDateString('en-IN', {weekday:'long', year:'numeric', month:'long', day:'numeric'})}</div>

            <div className="space-y-4">
              <div>
                <label className="label">Pre-market Analysis</label>
                <textarea className="input text-xs min-h-[80px] resize-none" placeholder="What are you watching today? Levels, news, sentiment..."></textarea>
              </div>

              <div>
                <label className="label">Emotional State (1-10)</label>
                <input type="range" min="1" max="10" className="w-full accent-primary" />
                <div className="flex justify-between text-[0.6rem] text-tx-f font-mono mt-1"><span>1: Anxious</span><span>5: Neutral</span><span>10: Confident</span></div>
              </div>

              <div>
                <label className="label">Post-market Lessons</label>
                <textarea className="input text-xs min-h-[100px] resize-none" placeholder="What did you do well? What mistakes were made?"></textarea>
              </div>

              <button className="btn-ghost w-full">Save Entry</button>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
