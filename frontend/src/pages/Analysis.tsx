import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { brain, addTrade, indmoney, screener } from '../lib/api';
import { Activity, AlertTriangle, Target, TrendingDown, TrendingUp, Zap, X, Check, Calculator, BarChart2 } from 'lucide-react';
import TradingViewWidget from '../components/TradingViewWidget';

export default function Analysis() {
  const [symbol, setSymbol] = useState('NIFTY');
  const [capital, setCapital] = useState(100000);
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);
  const [modal, setModal] = useState<{ isOpen: boolean; type: 'paper' | 'indmoney'; signal: any | null }>({
    isOpen: false,
    type: 'paper',
    signal: null
  });

  const { data: analysis, isLoading, refetch, isFetching } = useQuery<any>({
    queryKey: ['brainAnalysis', symbol, capital],
    queryFn: () => brain.analyze(symbol, capital),
    refetchOnWindowFocus: false,
  });

  const { data: screenerData, isLoading: isScreenerLoading, refetch: refetchScreener } = useQuery<any>({
    queryKey: ['screenerRun'],
    queryFn: () => screener.run(),
    refetchOnWindowFocus: false,
  });

  const showToast = (msg: string, type: 'success' | 'error') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 5000);
  };

  const paperTradeMutation = useMutation({
    mutationFn: async (signal: any) => {
      const payload = {
        symbol: signal.symbol,
        trade_type: signal.action,
        instrument: signal.instrument,
        qty: signal.suggested_qty || signal.legs?.[0]?.qty || 50,
        entry_price: signal.entry_price,
        stop_loss: signal.stop_loss,
        target: signal.target_price,
        setup: signal.strategy_name || signal.setup,
        notes: `Rationale: ${signal.rationale}`
      };
      return addTrade(payload);
    },
    onSuccess: () => {
      showToast("Strategy saved to Paper Trade Journal!", "success");
      setModal({ isOpen: false, type: 'paper', signal: null });
    },
    onError: (err: any) => {
      showToast(`Paper Trade failed: ${err.message}`, "error");
      setModal({ isOpen: false, type: 'paper', signal: null });
    }
  });

  const confirmAction = () => {
    if (!modal.signal) return;
    if (modal.type === 'paper') paperTradeMutation.mutate(modal.signal);
  };

  return (
    <div className="space-y-6 relative h-[calc(100vh-8rem)] flex flex-col">
      {/* Toast & Modals Code (Unchanged) */}
      {toast && (
        <div className={`fixed top-4 right-4 p-4 rounded shadow-lg flex items-center gap-3 z-50 border ${toast.type === 'success' ? 'bg-surface border-gain/20 text-gain' : 'bg-surface border-loss/20 text-loss'}`}>
          {toast.type === 'success' ? <Check className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          <p className="font-medium text-sm">{toast.msg}</p>
        </div>
      )}

      {modal.isOpen && modal.signal && (
        <div className="fixed inset-0 bg-bg/80 backdrop-blur-sm z-40 flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-lg overflow-hidden">
            <div className={`p-4 border-b border-border flex items-center gap-3 bg-s2`}>
              <Target className="text-primary w-6 h-6" />
              <h2 className="text-lg font-bold text-tx">Confirm Paper Trade</h2>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-tx-m text-sm">This will record the strategy in your local Paper Trading journal for forward testing and autonomous tracking.</p>
              <div className="bg-bg border border-border rounded-lg p-4">
                <div className="flex justify-between items-center pb-2 border-b border-border/50 mb-2">
                  <span className="font-semibold text-tx">{modal.signal.strategy_name || modal.signal.setup}</span>
                  <span className="text-xs font-mono text-tx-m">{modal.signal.symbol}</span>
                </div>
                <div className="font-mono text-sm text-tx-m">Qty: {modal.signal.suggested_qty || 1}</div>
                <div className="font-mono text-sm text-tx-m">Entry: ₹{modal.signal.entry_price || modal.signal.close}</div>
              </div>
            </div>
            <div className="p-4 border-t border-border flex justify-end gap-3 bg-s2">
              <button onClick={() => setModal({ isOpen: false, type: 'paper', signal: null })} className="px-4 py-2 rounded text-sm font-medium text-tx-m hover:text-tx hover:bg-border transition-colors">Cancel</button>
              <button onClick={confirmAction} className="px-4 py-2 rounded text-sm font-bold bg-primary hover:bg-pr-d text-bg">Add to Journal</button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-tx">Chart & Execution Engine</h1>
          <p className="text-tx-m">Advanced Charting + NEXUS Quant Brain</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-surface border border-border rounded-md px-3 py-1.5 focus-within:border-primary">
            <span className="text-tx-m text-sm">₹</span>
            <input 
              type="number" value={capital} onChange={(e) => setCapital(Number(e.target.value))}
              className="bg-transparent border-none outline-none text-tx text-sm w-24" placeholder="Capital"
            />
          </div>
          <select 
            value={symbol} onChange={(e) => setSymbol(e.target.value)}
            className="bg-surface text-tx border border-border rounded-md px-3 py-1.5 text-sm outline-none focus:border-primary"
          >
            <option value="NIFTY">NIFTY 50</option>
            <option value="BANKNIFTY">BANK NIFTY</option>
            <optgroup label="Swing Universe">
              <option value="RELIANCE">RELIANCE</option>
              <option value="HDFCBANK">HDFCBANK</option>
              <option value="INFY">INFY</option>
              <option value="TCS">TCS</option>
              <option value="TATAMOTORS">TATAMOTORS</option>
            </optgroup>
          </select>
          <button onClick={() => {refetch(); refetchScreener();}} className="px-4 py-1.5 bg-primary hover:bg-pr-d text-bg rounded font-medium flex items-center gap-2 text-sm shadow-sm">
            <Zap className={`w-4 h-4 ${isFetching ? 'animate-pulse' : ''}`} />
            {isFetching ? 'Crunching...' : 'Analyze'}
          </button>
        </div>
      </div>

      {/* Split Layout */}
      <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-6">

        {/* Left Side: TradingView Widget */}
        <div className="flex-1 h-[400px] lg:h-full relative rounded-xl group">
          <div className="absolute top-2 left-2 z-10 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="bg-bg/80 backdrop-blur text-tx-m text-xs px-2 py-1 rounded border border-border flex items-center gap-1">
              <BarChart2 className="w-3 h-3"/> Live Data
            </div>
          </div>
          <TradingViewWidget symbol={symbol} />
        </div>

        {/* Right Side: AI Signals & Screener */}
        <div className="w-full lg:w-[450px] flex flex-col gap-6 overflow-y-auto pr-2 pb-6">

          {/* Section: Intraday Options Brain */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-tx-m uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-primary" /> Intraday Setups (Options)
            </h3>
            {isLoading ? (
              <div className="p-6 border border-border bg-s2/50 h-32 animate-pulse rounded-lg"></div>
            ) : analysis?.suggestions?.length > 0 ? (
              analysis.suggestions.map((signal: any, idx: number) => (
                <div key={idx} className="border border-border rounded-xl shadow-sm bg-surface p-4 space-y-3">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                      {signal.action === 'BUY' ? <TrendingUp className="w-4 h-4 text-gain" /> : <TrendingDown className="w-4 h-4 text-warn" />}
                      <span className="font-bold text-sm text-tx">{signal.strategy_name}</span>
                    </div>
                    <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-0.5 rounded">{(signal.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                  <p className="text-xs text-tx-m border-l-2 border-primary/30 pl-2 leading-relaxed">{signal.rationale}</p>

                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-bg p-2 rounded border border-border/50 text-center">
                      <div className="text-[10px] text-tx-m uppercase">Entry</div>
                      <div className="font-mono text-xs text-tx">₹{signal.entry_price}</div>
                    </div>
                    <div className="bg-gain/5 p-2 rounded border border-gain/10 text-center">
                      <div className="text-[10px] text-gain uppercase">Target</div>
                      <div className="font-mono text-xs text-gain">₹{signal.target_price}</div>
                    </div>
                    <div className="bg-loss/5 p-2 rounded border border-loss/10 text-center">
                      <div className="text-[10px] text-loss uppercase">Stop</div>
                      <div className="font-mono text-xs text-loss">₹{signal.stop_loss}</div>
                    </div>
                  </div>

                  <button 
                    onClick={() => setModal({ isOpen: true, type: 'paper', signal })}
                    className="w-full py-2 bg-s2 hover:bg-border text-tx rounded text-xs font-medium transition-colors"
                  >
                    Track in Journal
                  </button>
                </div>
              ))
            ) : (
              <div className="text-sm text-tx-m bg-surface border border-border p-4 rounded-xl text-center">
                No active setups for {symbol} currently.
              </div>
            )}
          </div>

          {/* Section: Swing Screener */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-tx-m uppercase tracking-wider flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue" /> Multi-Day Swing Screener
            </h3>
            {isScreenerLoading ? (
              <div className="p-6 border border-border bg-s2/50 h-32 animate-pulse rounded-lg"></div>
            ) : screenerData?.shortlist?.length > 0 ? (
              screenerData.shortlist.map((setup: any, idx: number) => (
                <div key={idx} 
                  className={`border border-border hover:border-blue/50 cursor-pointer transition-colors rounded-xl shadow-sm bg-surface p-4 space-y-3 ${symbol === setup.symbol ? 'ring-2 ring-blue/50' : ''}`}
                  onClick={() => setSymbol(setup.symbol)} // Clicking it loads it in TradingView!
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-sm text-tx font-mono">{setup.symbol}</span>
                    <span className="text-xs text-blue bg-blue/10 px-2 py-0.5 rounded border border-blue/20">{setup.setup}</span>
                  </div>
                  <div className="flex justify-between text-xs text-tx-m font-mono">
                    <span>CMP: ₹{setup.close}</span>
                    <span>RSI: {setup.rsi}</span>
                  </div>
                  <p className="text-xs text-tx-m leading-relaxed">{setup.rationale}</p>

                  <button 
                    onClick={(e) => { e.stopPropagation(); setModal({ isOpen: true, type: 'paper', signal: {...setup, action: 'BUY', instrument: 'EQ', entry_price: setup.close, target_price: (setup.close*1.15).toFixed(2), stop_loss: (setup.close*0.95).toFixed(2)} }) }}
                    className="w-full py-2 bg-s2 hover:bg-border text-tx rounded text-xs font-medium transition-colors"
                  >
                    Track Swing Trade
                  </button>
                </div>
              ))
            ) : (
              <div className="text-sm text-tx-m bg-surface border border-border p-4 rounded-xl text-center">
                No high-probability swing setups found in the top 20 liquid stocks.
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
