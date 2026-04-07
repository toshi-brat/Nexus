import { useStore } from '../../store'
import { fmt, colorPnl } from '../../lib/utils'

export default function Header() {
  const indices = useStore(s => s.indices)
  const showIndices = ['NIFTY 50', 'BANKNIFTY', 'SENSEX', 'INDIA VIX']

  return (
    <header className="h-16 border-b border-border bg-surface/50 backdrop-blur flex items-center px-6 gap-6 overflow-x-auto shrink-0">
      {showIndices.map(name => {
        const data = indices[name]
        if (!data) return (
          <div key={name} className="flex flex-col gap-1 min-w-[120px]">
            <span className="text-xs text-tx-m font-medium">{name}</span>
            <div className="h-4 w-16 shimmer rounded"></div>
          </div>
        )
        return (
          <div key={name} className="flex flex-col min-w-[120px] shrink-0">
            <span className="text-xs text-tx-m font-medium mb-0.5">{name}</span>
            <div className="flex items-baseline gap-2">
              <span className="num font-bold text-[0.95rem]">{data.last.toLocaleString('en-IN', {minimumFractionDigits:2})}</span>
              <span className={`num text-xs ${colorPnl(data.pct)}`}>
                {fmt.pct(data.pct)}
              </span>
            </div>
          </div>
        )
      })}
    </header>
  )
}
