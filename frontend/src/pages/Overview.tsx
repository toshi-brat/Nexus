import { useQuery } from '@tanstack/react-query'
import { marketApi, sentimentApi } from '../lib/api'
import { fmt, colorPnl } from '../lib/utils'
import { Activity, TrendingUp, TrendingDown, Clock, Newspaper } from 'lucide-react'

export default function Overview() {
  const { data: movers, isLoading: loadMovers } = useQuery({ queryKey: ['movers'], queryFn: marketApi.getMovers })
  const { data: optionChain, isLoading: loadChain } = useQuery({ queryKey: ['option-chain', 'NIFTY'], queryFn: () => marketApi.getOptionChain('NIFTY') })
  const { data: sentiment, isLoading: loadSent } = useQuery({ queryKey: ['sentiment'], queryFn: sentimentApi.getSentiment })

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Activity className="text-primary" size={24} />
        <h1 className="text-2xl font-bold tracking-tight">Market Overview</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Top Movers */}
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2"><TrendingUp size={20} className="text-gain" /> Top Gainers & Losers</h2>
            <span className="text-xs text-tx-m">NIFTY 50</span>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-3">
              {loadMovers ? [...Array(5)].map((_,i) => <div key={i} className="h-10 shimmer rounded"></div>) : 
               movers?.gainers?.map((g: any) => (
                <div key={g.symbol} className="flex justify-between items-center p-2 rounded hover:bg-s2 border border-transparent hover:border-border transition-all">
                  <span className="font-semibold text-sm">{g.symbol}</span>
                  <div className="text-right">
                    <div className="num text-sm">{fmt.price(g.lastPrice)}</div>
                    <div className="num text-xs text-gain">{fmt.pct(g.pChange)}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="space-y-3 border-l border-border pl-6">
              {loadMovers ? [...Array(5)].map((_,i) => <div key={i} className="h-10 shimmer rounded"></div>) : 
               movers?.losers?.map((l: any) => (
                <div key={l.symbol} className="flex justify-between items-center p-2 rounded hover:bg-s2 border border-transparent hover:border-border transition-all">
                  <span className="font-semibold text-sm">{l.symbol}</span>
                  <div className="text-right">
                    <div className="num text-sm">{fmt.price(l.lastPrice)}</div>
                    <div className="num text-xs text-loss">{fmt.pct(l.pChange)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sentiment Snap */}
        <div className="card p-5 bg-gradient-to-br from-s2 to-bg flex flex-col items-center justify-center">
          <h2 className="text-lg font-semibold mb-6 self-start flex items-center gap-2"><Activity size={20} className="text-primary"/> Market Mood</h2>
          {loadSent ? <div className="h-40 w-40 rounded-full shimmer" /> : (
            <>
              <div className="relative flex items-center justify-center w-40 h-40 rounded-full border-4 border-s3 mb-6">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="80" cy="80" r="74" fill="none" stroke="#252730" strokeWidth="8" />
                  <circle cx="80" cy="80" r="74" fill="none" stroke={sentiment?.overall_score > 0 ? '#22d98a' : '#ff4d6d'} 
                    strokeWidth="8" strokeDasharray="465" 
                    strokeDashoffset={465 - (465 * (Math.abs(sentiment?.overall_score || 0) * 100)) / 100} 
                    className="transition-all duration-1000 ease-out" />
                </svg>
                <div className="absolute text-center">
                  <div className="text-3xl font-bold font-mono">{((sentiment?.overall_score || 0) * 100).toFixed(0)}</div>
                  <div className={`text-xs mt-1 uppercase tracking-wider font-semibold ${
                    sentiment?.overall_score > 0 ? 'text-gain' : 'text-loss'
                  }`}>{sentiment?.label}</div>
                </div>
              </div>
              <div className="flex gap-4 w-full justify-between px-4 text-sm font-mono border-t border-border pt-4">
                <span className="text-gain">Bull: {sentiment?.bullish_pct}%</span>
                <span className="text-tx-m">Neu: {sentiment?.neutral_pct}%</span>
                <span className="text-loss">Bear: {sentiment?.bearish_pct}%</span>
              </div>
            </>
          )}
        </div>

      </div>

      {/* Option Chain Snippet */}
      <div className="card p-0 overflow-hidden">
        <div className="p-5 border-b border-border flex justify-between items-center bg-s2/50">
          <h2 className="text-lg font-semibold flex items-center gap-2"><Clock size={20} className="text-blue" /> NIFTY Option Chain (ATM ± 2)</h2>
          {optionChain?.records?.underlyingValue && <span className="badge-neutral border border-border">Spot: {optionChain.records.underlyingValue}</span>}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-s3 text-tx-m text-xs uppercase">
              <tr>
                <th className="p-3 text-center" colSpan={3}>CALLS</th>
                <th className="p-3 text-center border-x border-border w-24">STRIKE</th>
                <th className="p-3 text-center" colSpan={3}>PUTS</th>
              </tr>
              <tr className="border-y border-border">
                <th className="p-2 pl-4">OI (Lakhs)</th><th className="p-2">IV</th><th className="p-2 text-right pr-4">LTP</th>
                <th className="p-2 border-x border-border"></th>
                <th className="p-2 pl-4">LTP</th><th className="p-2">IV</th><th className="p-2 text-right pr-4">OI (Lakhs)</th>
              </tr>
            </thead>
            <tbody>
              {loadChain ? [...Array(5)].map((_,i) => <tr key={i}><td colSpan={7} className="p-3"><div className="h-6 shimmer rounded"></div></td></tr>) : 
               optionChain?.records?.data?.slice(3,8).map((d: any, i: number) => {
                 const spot = optionChain.records.underlyingValue;
                 const isAtm = Math.abs(d.strikePrice - spot) < 50;
                 return (
                  <tr key={i} className={`table-row ${isAtm ? 'bg-primary/5 font-semibold' : ''}`}>
                    <td className="p-2 pl-4 num">{(d.CE.openInterest / 100000).toFixed(1)}</td>
                    <td className="p-2 num">{d.CE.impliedVolatility}</td>
                    <td className="p-2 text-right pr-4 num font-medium text-gain">{fmt.price(d.CE.lastPrice)}</td>

                    <td className="p-2 text-center border-x border-border num font-bold text-[0.9rem] bg-s2/30">{d.strikePrice}</td>

                    <td className="p-2 pl-4 num font-medium text-loss">{fmt.price(d.PE.lastPrice)}</td>
                    <td className="p-2 num">{d.PE.impliedVolatility}</td>
                    <td className="p-2 text-right pr-4 num">{(d.PE.openInterest / 100000).toFixed(1)}</td>
                  </tr>
                 )
               })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
