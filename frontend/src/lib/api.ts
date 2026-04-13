/* NEXUS — API client with frontend-friendly normalization layers */

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

type RecordLike = Record<string, unknown>

const toNumber = (value: unknown): number | null => {
  if (typeof value === 'number' && !Number.isNaN(value)) return value
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value)
    return Number.isNaN(parsed) ? null : parsed
  }
  return null
}

const firstNumber = (item: RecordLike, keys: string[]): number | null => {
  for (const key of keys) {
    const value = toNumber(item[key])
    if (value !== null) return value
  }
  return null
}

const sentimentLabel = (value: unknown): 'bullish' | 'bearish' | 'neutral' => {
  const raw = String(value ?? '').toLowerCase()
  if (raw.includes('pos') || raw.includes('bull')) return 'bullish'
  if (raw.includes('neg') || raw.includes('bear')) return 'bearish'
  return 'neutral'
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`)
  if (!r.ok) {
    let detail = `${r.status} ${r.statusText}`
    try {
      const body = await r.json()
      if (body && typeof body === 'object' && typeof body.detail === 'string') {
        detail = body.detail
      }
    } catch {
      // Ignore JSON parsing errors and fall back to status text.
    }
    throw new Error(detail)
  }
  return r.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    let detail = `${r.status} ${r.statusText}`
    try {
      const payload = await r.json()
      if (payload && typeof payload === 'object' && typeof payload.detail === 'string') {
        detail = payload.detail
      }
    } catch {
      // Ignore JSON parsing errors and fall back to status text.
    }
    throw new Error(detail)
  }
  return r.json()
}

async function del<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`, { method: 'DELETE' })
  if (!r.ok) {
    let detail = `${r.status} ${r.statusText}`
    try {
      const payload = await r.json()
      if (payload && typeof payload === 'object' && typeof payload.detail === 'string') {
        detail = payload.detail
      }
    } catch {
      // Ignore JSON parsing errors and fall back to status text.
    }
    throw new Error(detail)
  }
  return r.json()
}

function normalizeMovers(data: RecordLike) {
  const normalizeList = (items: unknown) =>
    Array.isArray(items)
      ? items.map((item) => {
          const row = item as RecordLike
          return {
            ...row,
            symbol: String(row.symbol ?? row.name ?? '--'),
            lastPrice: firstNumber(row, ['lastPrice', 'ltp', 'last', 'close']) ?? 0,
            pChange: firstNumber(row, ['pChange', 'pct', 'percentChange']) ?? 0,
          }
        })
      : []

  return {
    gainers: normalizeList(data.gainers),
    losers: normalizeList(data.losers),
  }
}

function normalizeOptionChain(data: RecordLike) {
  if (data.records && typeof data.records === 'object') return data

  const spot = toNumber(data.spot) ?? 0
  const chain = Array.isArray(data.chain) ? data.chain : []

  return {
    records: {
      underlyingValue: spot,
      data: chain.map((item) => {
        const row = item as RecordLike
        return {
          strikePrice: firstNumber(row, ['strike', 'strikePrice']) ?? 0,
          CE: {
            openInterest: firstNumber(row, ['ce_oi', 'ceOpenInterest']) ?? 0,
            impliedVolatility: firstNumber(row, ['ce_iv', 'ceImpliedVolatility']) ?? 0,
            lastPrice: firstNumber(row, ['ce_ltp', 'ceLastPrice']) ?? 0,
          },
          PE: {
            openInterest: firstNumber(row, ['pe_oi', 'peOpenInterest']) ?? 0,
            impliedVolatility: firstNumber(row, ['pe_iv', 'peImpliedVolatility']) ?? 0,
            lastPrice: firstNumber(row, ['pe_ltp', 'peLastPrice']) ?? 0,
          },
        }
      }),
    },
  }
}

function normalizeSentiment(data: RecordLike) {
  const distribution =
    data.distribution && typeof data.distribution === 'object'
      ? (data.distribution as RecordLike)
      : {}
  const positive = toNumber(data.positive) ?? toNumber(distribution.bullish) ?? 0
  const negative = toNumber(data.negative) ?? toNumber(distribution.bearish) ?? 0
  const neutral = toNumber(data.neutral) ?? toNumber(distribution.neutral) ?? 0
  const total = toNumber(data.total) ?? positive + negative + neutral
  const pct = (count: number) => (total > 0 ? Math.round((count / total) * 100) : 0)

  const normalizeNewsItems = (items: unknown) =>
    Array.isArray(items)
      ? items.map((item) => {
          const row = item as RecordLike
          return {
            title: String(row.title ?? row.text ?? ''),
            source: String(row.source ?? 'News'),
            url: String(row.url ?? '#'),
            published:
              typeof row.published === 'string'
                ? row.published
                : typeof row.timestamp === 'string'
                  ? row.timestamp
                  : new Date().toISOString(),
            sentiment: sentimentLabel(row.sentiment_label ?? row.sentiment ?? row.score),
          }
        })
      : []

  const normalizeRedditItems = (items: unknown) =>
    Array.isArray(items)
      ? items.map((item) => {
          const row = item as RecordLike
          return {
            title: String(row.title ?? row.text ?? ''),
            subreddit: String(row.subreddit ?? row.sub ?? row.source ?? 'reddit'),
            url: String(row.url ?? '#'),
            comments: firstNumber(row, ['comments', 'num_comments']) ?? 0,
            score: firstNumber(row, ['score']) ?? 0,
            sentiment: sentimentLabel(row.sentiment_label ?? row.sentiment ?? row.score),
          }
        })
      : []

  const overallScore = toNumber(data.score) ?? toNumber(data.raw_score) ?? 0

  return {
    overall_score: overallScore,
    label:
      typeof data.label === 'string'
        ? data.label
        : overallScore > 0.1
          ? 'POSITIVE'
          : overallScore < -0.1
            ? 'NEGATIVE'
            : 'NEUTRAL',
    bullish_pct: pct(positive),
    bearish_pct: pct(negative),
    neutral_pct: pct(neutral),
    news_items: normalizeNewsItems(data.news),
    reddit_items: normalizeRedditItems(data.reddit ?? data.social),
  }
}

function normalizePortfolio(data: RecordLike) {
  const rawHoldings = Array.isArray(data.holdings) ? data.holdings : []
  const rawSummary = (data.summary ?? {}) as RecordLike
  const rawFunds = (data.funds ?? {}) as RecordLike

  const holdings = rawHoldings.map((item) => {
    const row = item as RecordLike
    const qty = firstNumber(row, ['qty', 'quantity', 'total_qty', 'net_qty']) ?? 0
    const avgPrice = firstNumber(row, ['avg_price', 'average_price', 'dp_avg_price']) ?? 0
    const ltp = firstNumber(row, ['ltp', 'last_price', 'current_price'])
    const invested = qty * avgPrice
    const current = ltp !== null ? qty * ltp : null
    const pnl = current !== null ? current - invested : null
    const pnlPct = pnl !== null && invested > 0 ? (pnl / invested) * 100 : null

    return {
      symbol: String(row.symbol ?? row.tradingsymbol ?? row.ticker ?? '--'),
      qty,
      avg_price: avgPrice,
      ltp,
      invested,
      current,
      pnl,
      pnl_pct: pnlPct,
    }
  })

  const totalInvested =
    firstNumber(rawSummary, ['total_invested', 'invested_value']) ??
    holdings.reduce((sum, row) => sum + row.invested, 0)

  const totalPnl =
    firstNumber(rawSummary, ['total_pnl']) ??
    firstNumber(rawFunds, ['unrealized_pnl']) ??
    holdings.reduce((sum, row) => sum + (row.pnl ?? 0), 0)

  const holdingsCurrent = holdings.reduce((sum, row) => sum + (row.current ?? 0), 0)
  const totalCurrent =
    firstNumber(rawSummary, ['total_current', 'current_value']) ??
    (holdingsCurrent > 0 ? holdingsCurrent : totalInvested + totalPnl)

  return {
    holdings,
    funds: rawFunds,
    summary: {
      total_invested: totalInvested,
      total_current: totalCurrent,
      total_pnl: totalPnl,
      total_pnl_pct:
        firstNumber(rawSummary, ['total_pnl_pct']) ??
        (totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0),
      day_pnl: firstNumber(rawSummary, ['day_pnl']) ?? 0,
      holdings_count: firstNumber(rawSummary, ['holdings_count']) ?? holdings.length,
      open_positions: firstNumber(rawSummary, ['open_positions']) ?? 0,
      cash_balance: firstNumber(rawFunds, ['withdrawal_balance', 'sod_balance']),
      broker: 'indmoney',
    },
    fetched_at: typeof data.fetched_at === 'string' ? data.fetched_at : null,
  }
}

export const marketApi = {
  getOverview: (): Promise<any> => get('/api/market/indices'),
  getMovers: async (): Promise<any> => normalizeMovers(await get<RecordLike>('/api/market/movers')),
  getOptionChain: async (symbol: string): Promise<any> =>
    normalizeOptionChain(await get<RecordLike>(`/api/market/option-chain/${encodeURIComponent(symbol)}`)),
}

export const sentimentApi = {
  getSentiment: async (): Promise<any> => normalizeSentiment(await get<RecordLike>('/sentiment')),
}

export const portfolioApi = {
  getLiveHoldings: async (): Promise<any> => normalizePortfolio(await get<RecordLike>('/indmoney/portfolio')),
}

export const tradesApi = {
  getTrades: (): Promise<any[]> => get<any[]>('/api/trades'),
  getStats: (): Promise<any> => get<any>('/api/trades/stats'),
  addTrade: (trade: unknown): Promise<any> => post('/api/trades', trade),
  deleteTrade: (tradeId: number): Promise<{ ok: boolean }> => del(`/api/trades/${tradeId}`),
}

export const fetchMarketOverview = marketApi.getOverview
export const fetchOptionChain = marketApi.getOptionChain
export const fetchSentiment = sentimentApi.getSentiment
export const fetchPortfolio = portfolioApi.getLiveHoldings
export const fetchTrades = tradesApi.getTrades
export const addTrade = tradesApi.addTrade

export const indmoney = {
  portfolio: portfolioApi.getLiveHoldings,
  holdings: () => get('/indmoney/holdings'),
  positions: () => get('/indmoney/positions'),
  funds: () => get('/indmoney/funds'),
  profile: () => get('/indmoney/profile'),
  quotes: (symbols: string[]) => get(`/indmoney/quotes?symbols=${symbols.join(',')}`),
  ltp: (symbols: string[]) => get(`/indmoney/ltp?symbols=${symbols.join(',')}`),
  optionChain: (symbol: string, expiry: string) =>
    get(`/indmoney/option-chain?symbol=${encodeURIComponent(symbol)}&expiry=${encodeURIComponent(expiry)}`),
  expiries: (symbol: string) => get(`/indmoney/option-chain/expiries?symbol=${encodeURIComponent(symbol)}`),
  historical: (symbol: string, interval = '1d', from?: string, to?: string) =>
    get(`/indmoney/historical?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(interval)}${from ? `&from_date=${encodeURIComponent(from)}` : ''}${to ? `&to_date=${encodeURIComponent(to)}` : ''}`),
  orderBook: () => get('/indmoney/orders'),
  placeOrder: (order: unknown) => post('/indmoney/orders', order),
  cancelOrder: (id: string) => post(`/indmoney/orders/${encodeURIComponent(id)}/cancel`, {}),
  tradeHistory: () => get('/indmoney/trades'),
  placeGTT: (gtt: unknown) => post('/indmoney/gtt', gtt),
  wsInfo: () => get('/indmoney/ws-info'),
}


// ── Brain (Quantitative Engine) ────────────────────────────────────────────
export const screener = {
  run: () => get('/screener')
};

export const brain = {
  analyze: (symbol: string, capital: number) => get(`/brain/analyze/${symbol}?capital=${capital}`),
};

// ── Strategy Scanner ───────────────────────────────────────────────────────
export const strategyApi = {
  runScan: (params: {
    timeframe?: string
    days?: number
    capital?: number
    strategy?: string
    save?: boolean
  }) => {
    const qs = new URLSearchParams()
    if (params.timeframe) qs.set('timeframe', params.timeframe)
    if (params.days)      qs.set('days', String(params.days))
    if (params.capital)   qs.set('capital', String(params.capital))
    if (params.strategy)  qs.set('strategy', params.strategy)
    qs.set('save', String(params.save ?? true))
    return get<any>(`/brain/scan?${qs.toString()}`)
  },

  getHistory: (params?: { strategy?: string; symbol?: string; outcome?: string; limit?: number }) => {
    const qs = new URLSearchParams()
    if (params?.strategy) qs.set('strategy', params.strategy)
    if (params?.symbol)   qs.set('symbol', params.symbol)
    if (params?.outcome)  qs.set('outcome', params.outcome)
    if (params?.limit)    qs.set('limit', String(params.limit))
    return get<any>(`/brain/scan/history?${qs.toString()}`)
  },

  getPerformance: () => get<any>('/brain/scan/performance'),
}
