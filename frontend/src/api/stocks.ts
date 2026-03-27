import { useQuery } from '@tanstack/react-query'

export interface StockFilters {
  index?: string
  sector?: string
  rsi_min?: number
  rsi_max?: number
  pe_min?: number
  pe_max?: number
}

const BASE = '/api'

export function useStocks(filters: StockFilters = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v != null && v !== '') params.set(k, String(v))
  })
  const query = params.toString()
  return useQuery<any[]>({
    queryKey: ['stocks', filters],
    queryFn: () => fetch(`${BASE}/stocks${query ? '?' + query : ''}`).then(r => r.json()),
  })
}

export function useStock(ticker: string | undefined) {
  return useQuery<any>({
    queryKey: ['stock', ticker],
    queryFn: () => fetch(`${BASE}/stocks/${ticker}`).then(r => r.json()),
    enabled: !!ticker,
  })
}
