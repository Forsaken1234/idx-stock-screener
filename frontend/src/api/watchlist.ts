import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function useWatchlist() {
  return useQuery<string[]>({
    queryKey: ['watchlist'],
    queryFn: () => fetch('/api/watchlist').then(r => r.json()).then((d: any) => d.tickers),
  })
}

export function useAddToWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ticker: string) => fetch(`/api/watchlist/${ticker}`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ticker: string) => fetch(`/api/watchlist/${ticker}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })
}
