import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 10_000 })

export const marketApi = {
  getIndices: ()              => api.get('/market/indices').then(r => r.data),
  getOptionChain: (sym: string) => api.get(`/market/option-chain/${sym}`).then(r => r.data),
  getMovers: ()               => api.get('/market/movers').then(r => r.data),
}

export const sentimentApi = {
  getSentiment: () => api.get('/sentiment').then(r => r.data),
  getNews:      () => api.get('/sentiment/news').then(r => r.data),
}

export const portfolioApi = {
  getLiveHoldings: () => api.get('/portfolio/live').then(r => r.data),
  getHoldings:     () => api.get('/portfolio/holdings').then(r => r.data),
  addHolding: (data: any) => api.post('/portfolio/holdings', data).then(r => r.data),
  deleteHolding: (sym: string) => api.delete(`/portfolio/holdings/${sym}`).then(r => r.data),
}

export const tradesApi = {
  getTrades:  (status?: string) => api.get('/trades', { params: { status } }).then(r => r.data),
  createTrade: (data: any)      => api.post('/trades', data).then(r => r.data),
  updateTrade: (id: number, data: any) => api.put(`/trades/${id}`, data).then(r => r.data),
  deleteTrade: (id: number)     => api.delete(`/trades/${id}`).then(r => r.data),
  getStats:    ()               => api.get('/trades/stats').then(r => r.data),
  getJournal:  ()               => api.get('/trades/journal').then(r => r.data),
  upsertJournal: (data: any)    => api.post('/trades/journal', data).then(r => r.data),
}

export default api
