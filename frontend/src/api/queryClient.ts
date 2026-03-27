import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,       // 5 minutes
      refetchInterval: 5 * 60 * 1000,  // auto-refetch every 5 min
      retry: 2,
    },
  },
})
