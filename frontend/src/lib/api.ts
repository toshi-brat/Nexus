/* NEXUS — API client (auto-falls back to demo data when backend is offline) */

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

// ── Market ─────────────────────────────────────────────────────────────────
export const fetchMarketOverview   = () => get("/market/overview");
export const fetchOptionChain      = (sym: string, exp: string) =>
  get(`/market/option-chain?symbol=${sym}&expiry=${exp}`);

// ── Sentiment ──────────────────────────────────────────────────────────────
export const fetchSentiment        = () => get("/sentiment/summary");

// ── Portfolio (generic) ────────────────────────────────────────────────────
export const fetchPortfolio        = () => get("/portfolio");

// ── Trades (paper) ────────────────────────────────────────────────────────
export const fetchTrades           = () => get("/trades");
export const addTrade              = (trade: unknown) => post("/trades", trade);

// ── IndMoney / INDstocks ───────────────────────────────────────────────────
export const indmoney = {
  /** Full portfolio snapshot: holdings + positions + funds + summary KPIs */
  portfolio:   () => get("/indmoney/portfolio"),
  holdings:    () => get("/indmoney/holdings"),
  positions:   () => get("/indmoney/positions"),
  funds:       () => get("/indmoney/funds"),
  profile:     () => get("/indmoney/profile"),

  /** Market data */
  quotes:      (symbols: string[]) => get(`/indmoney/quotes?symbols=${symbols.join(",")}`),
  ltp:         (symbols: string[]) => get(`/indmoney/ltp?symbols=${symbols.join(",")}`),
  optionChain: (symbol: string, expiry: string) =>
    get(`/indmoney/option-chain?symbol=${symbol}&expiry=${expiry}`),
  expiries:    (symbol: string) => get(`/indmoney/option-chain/expiries?symbol=${symbol}`),
  historical:  (symbol: string, interval = "1d", from?: string, to?: string) =>
    get(`/indmoney/historical?symbol=${symbol}&interval=${interval}${from ? "&from_date=" + from : ""}${to ? "&to_date=" + to : ""}`),

  /** Orders */
  orderBook:   () => get("/indmoney/orders"),
  placeOrder:  (order: unknown) => post("/indmoney/orders", order),
  cancelOrder: (id: string) => post(`/indmoney/orders/${id}/cancel`, {}),
  tradeHistory:() => get("/indmoney/trades"),

  /** Smart Orders */
  placeGTT:    (gtt: unknown) => post("/indmoney/gtt", gtt),

  /** WebSocket info */
  wsInfo:      () => get("/indmoney/ws-info"),
};
