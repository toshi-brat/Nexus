import { useEffect, useRef, memo } from 'react';

const TradingViewWidget = ({ symbol }: { symbol: string }) => {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;
    container.current.innerHTML = ''; // Clean up before re-mounting

    // Map NEXUS symbols to TradingView symbols
    let tvSymbol = `NSE:${symbol}`;
    if (symbol === 'NIFTY') tvSymbol = 'NSE:NIFTY';
    if (symbol === 'BANKNIFTY') tvSymbol = 'NSE:BANKNIFTY';

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.type = 'text/javascript';
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: tvSymbol,
      interval: "15",
      timezone: "Asia/Kolkata",
      theme: "dark",
      style: "1",
      locale: "en",
      enable_publishing: false,
      backgroundColor: "#171614", // Matches NEXUS dark mode surface
      gridColor: "#262523",
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: false,
      calendar: false,
      hide_volume: false,
      support_host: "https://www.tradingview.com",
      studies: [
        "Volume@tv-basicstudies",
        "RSI@tv-basicstudies",
        "MASimple@tv-basicstudies"
      ]
    });

    container.current.appendChild(script);
  }, [symbol]);

  return (
    <div className="w-full h-full bg-surface rounded-xl overflow-hidden border border-border shadow-sm" ref={container}></div>
  );
};

export default memo(TradingViewWidget);
