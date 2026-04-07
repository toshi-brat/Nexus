import { useQuery } from '@tanstack/react-query'
import { portfolioApi } from '../lib/api'
import { fmt, colorPnl } from '../lib/utils'
import { PieChart, Briefcase, RefreshCw, AlertCircle } from 'lucide-react'

export default function Portfolio() {
  const { data, isLoading, refetch } = useQuery({ queryKey: ['portfolio'], queryFn: portfolioApi.getLiveHoldings })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Briefcase className="text-primary" size={24} />
          <h1 className="text-2xl font-bold tracking-tight">Live Portfolio</h1>
        </div>
        <button onClick={() => refetch()} className="btn-ghost flex items-center gap-2"><RefreshCw size={16} /> Sync</button>
      </div>

      {isLoading ? <div className="h-64 shimmer rounded w-full"></div> : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card p-5 border-l-4 border-l-border">
              <span className="label">Total Invested</span>
              <div className="text-2xl font-bold num mt-1">{fmt.inr(data?.summary?.total_invested)}</div>
            </div>
            <div className="card p-5 border-l-4 border-l-blue">
              <span className="label">Current Value</span>
              <div className="text-2xl font-bold num mt-1">{fmt.inr(data?.summary?.total_current)}</div>
            </div>
            <div className={`card p-5 border-l-4 ${data?.summary?.total_pnl >= 0 ? 'border-l-gain' : 'border-l-loss'}`}>
              <span className="label">Total P&L</span>
              <div className={`text-2xl font-bold num mt-1 ${colorPnl(data?.summary?.total_pnl)}`}>
                {fmt.inr(data?.summary?.total_pnl)}
              </div>
            </div>
            <div className={`card p-5 border-l-4 ${data?.summary?.total_pnl_pct >= 0 ? 'border-l-gain' : 'border-l-loss'}`}>
              <span className="label">P&L %</span>
              <div className={`text-2xl font-bold num mt-1 ${colorPnl(data?.summary?.total_pnl_pct)}`}>
                {fmt.pct(data?.summary?.total_pnl_pct)}
              </div>
            </div>
          </div>

          {/* Broker Status */}
          {data?.summary?.broker === 'demo' && (
            <div className="bg-warn/10 border border-warn/20 text-warn p-4 rounded-lg flex items-start gap-3">
              <AlertCircle className="shrink-0 mt-0.5" size={20} />
              <div>
                <p className="font-semibold text-sm">Showing Demo Data</p>
                <p className="text-xs opacity-80 mt-1">Connect your broker (Zerodha/Upstox/Dhan) in the backend .env file and restart to see live holdings.</p>
              </div>
            </div>
          )}

          {/* Holdings Table */}
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-s2 text-tx-m text-xs uppercase border-b border-border">
                  <tr>
                    <th className="p-4 pl-6">Symbol</th>
                    <th className="p-4 text-right">Qty</th>
                    <th className="p-4 text-right">Avg Price</th>
                    <th className="p-4 text-right">LTP</th>
                    <th className="p-4 text-right">Inv. Value</th>
                    <th className="p-4 text-right">Cur. Value</th>
                    <th className="p-4 text-right pr-6">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.holdings?.map((h: any) => {
                    const inv = h.qty * h.avg_price;
                    const cur = h.qty * h.ltp;
                    return (
                    <tr key={h.symbol} className="table-row">
                      <td className="p-4 pl-6 font-semibold">{h.symbol}</td>
                      <td className="p-4 text-right num text-tx-m">{h.qty}</td>
                      <td className="p-4 text-right num">{fmt.price(h.avg_price)}</td>
                      <td className="p-4 text-right num font-medium">{fmt.price(h.ltp)}</td>
                      <td className="p-4 text-right num text-tx-m">{fmt.price(inv)}</td>
                      <td className="p-4 text-right num">{fmt.price(cur)}</td>
                      <td className={`p-4 text-right pr-6 num font-bold ${colorPnl(h.pnl)}`}>
                        {fmt.price(h.pnl)} <span className="text-xs opacity-70 ml-1">({fmt.pct(h.pnl_pct)})</span>
                      </td>
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
