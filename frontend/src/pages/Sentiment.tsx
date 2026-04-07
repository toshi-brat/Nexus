import { useQuery } from '@tanstack/react-query'
import { sentimentApi } from '../lib/api'
import { BarChart2, MessageSquare, Newspaper, ExternalLink } from 'lucide-react'

export default function Sentiment() {
  const { data, isLoading } = useQuery({ queryKey: ['sentiment-full'], queryFn: sentimentApi.getSentiment })

  if (isLoading) return <div className="p-8"><div className="h-12 w-48 shimmer rounded mb-8"></div><div className="h-96 shimmer rounded w-full"></div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <BarChart2 className="text-primary" size={24} />
        <h1 className="text-2xl font-bold tracking-tight">Market Sentiment Engine</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* News Stream */}
        <div className="card p-0 flex flex-col h-[70vh]">
          <div className="p-4 border-b border-border bg-s2 flex items-center justify-between shrink-0">
            <h2 className="font-semibold flex items-center gap-2"><Newspaper size={18} className="text-blue" /> Latest Financial News</h2>
            <span className="badge-neutral text-[0.6rem] uppercase">AI Scored</span>
          </div>
          <div className="overflow-y-auto p-4 space-y-3 flex-1">
            {data?.news_items?.map((n: any, i: number) => (
              <a key={i} href={n.url} target="_blank" rel="noopener noreferrer" 
                 className="block p-3 rounded-lg border border-border bg-s2 hover:border-primary/50 transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-mono text-tx-m">{n.source}</span>
                  <span className={`text-[0.65rem] px-2 py-0.5 rounded-full uppercase tracking-wider font-bold ${
                    n.sentiment === 'bullish' ? 'bg-gain/10 text-gain' : n.sentiment === 'bearish' ? 'bg-loss/10 text-loss' : 'bg-tx-m/10 text-tx-m'
                  }`}>{n.sentiment}</span>
                </div>
                <h3 className="text-sm font-medium text-tx group-hover:text-primary transition-colors leading-snug">{n.title}</h3>
                <div className="mt-2 text-xs text-tx-f flex justify-between items-center">
                  <span>{new Date(n.published).toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit'})}</span>
                  <ExternalLink size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </a>
            ))}
          </div>
        </div>

        {/* Reddit / Social Stream */}
        <div className="card p-0 flex flex-col h-[70vh]">
          <div className="p-4 border-b border-border bg-s2 flex items-center justify-between shrink-0">
            <h2 className="font-semibold flex items-center gap-2"><MessageSquare size={18} className="text-warn" /> Reddit Discussions</h2>
            <span className="badge-neutral text-[0.6rem] uppercase">r/IndiaInvestments & more</span>
          </div>
          <div className="overflow-y-auto p-4 space-y-3 flex-1">
            {data?.reddit_items?.map((n: any, i: number) => (
              <a key={i} href={n.url} target="_blank" rel="noopener noreferrer" 
                 className="block p-3 rounded-lg border border-border bg-s2 hover:border-warn/50 transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-mono text-tx-m">{n.subreddit}</span>
                  <span className={`text-[0.65rem] px-2 py-0.5 rounded-full uppercase tracking-wider font-bold ${
                    n.sentiment === 'bullish' ? 'bg-gain/10 text-gain' : n.sentiment === 'bearish' ? 'bg-loss/10 text-loss' : 'bg-tx-m/10 text-tx-m'
                  }`}>{n.sentiment}</span>
                </div>
                <h3 className="text-sm font-medium text-tx group-hover:text-warn transition-colors leading-snug">{n.title}</h3>
                <div className="mt-3 text-xs text-tx-f flex items-center gap-4">
                  <span className="flex items-center gap-1">⬆ {n.score}</span>
                  <span className="flex items-center gap-1">💬 {n.comments}</span>
                  <ExternalLink size={12} className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </a>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
