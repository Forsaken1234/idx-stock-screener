import { useQuery } from '@tanstack/react-query'

export function useMarket() {
  return useQuery<any>({
    queryKey: ['market'],
    queryFn: () => fetch('/api/market').then(r => r.json()),
  })
}
