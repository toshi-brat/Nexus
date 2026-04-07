import { LineChart, LayoutTemplate } from 'lucide-react'

export default function Analysis() {
  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col space-y-4">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <LineChart className="text-primary" size={24} />
          <h1 className="text-2xl font-bold tracking-tight">Chart Analysis</h1>
        </div>
        <div className="flex gap-2">
          <span className="badge-neutral border border-border flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-warn animate-pulse"></span> MCP Server Offline</span>
        </div>
      </div>

      <div className="flex-1 card p-0 border-border overflow-hidden bg-bg relative">
        {/* We use TradingView's Advanced Chart Widget iframe */}
        <iframe 
          title="TradingView"
          src={`https://s.tradingview.com/widgetembed/?frameElementId=tradingview_1&symbol=NSE:NIFTY&interval=15&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=111318&studies=[]&theme=dark&style=1&timezone=Asia/Kolkata`} 
          className="w-full h-full border-none"
          allowFullScreen
        ></iframe>
      </div>

      <div className="h-48 card p-4 shrink-0 overflow-y-auto">
        <h3 className="font-semibold text-sm flex items-center gap-2 mb-3"><LayoutTemplate size={16} className="text-tx-m"/> Key Levels & Notes</h3>
        <p className="text-xs text-tx-m max-w-2xl leading-relaxed">
          Use the chart above for technical analysis. When the MCP server is enabled (via backend <span className="font-mono bg-s2 px-1 rounded">TRADINGVIEW_MCP_URL</span>), you can query indicators programmatically and trigger automated alerts based on custom logic.
        </p>
      </div>
    </div>
  )
}
