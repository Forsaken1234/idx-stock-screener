import { useState } from 'react'
import { useStocks, StockFilters } from '../api/stocks'
import StockTable from '../components/StockTable'
import Layout from '../components/Layout'

export default function Screener() {
  const [filters, setFilters] = useState<StockFilters>({})
  const { data: stocks = [], isLoading } = useStocks(filters)
  const lastFetchedAt = stocks[0]?.fetched_at ?? null

  const set = (key: keyof StockFilters, val: string) =>
    setFilters(f => ({ ...f, [key]: val || undefined }))

  return (
    <Layout lastFetchedAt={lastFetchedAt}>
      <h2 className="text-xl font-semibold mb-6">Screener</h2>

      <div className="flex flex-wrap gap-3 mb-6">
        <select
          onChange={e => set('index', e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
        >
          <option value="">All Indices</option>
          <option value="LQ45">LQ45</option>
          <option value="IDX30">IDX30</option>
        </select>

        <input
          placeholder="PE max"
          type="number"
          onChange={e => set('pe_max', e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm w-24"
        />
        <input
          placeholder="RSI min"
          type="number"
          onChange={e => set('rsi_min', e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm w-24"
        />
        <input
          placeholder="RSI max"
          type="number"
          onChange={e => set('rsi_max', e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm w-24"
        />
      </div>

      {isLoading
        ? <p className="text-slate-400">Loading stocks…</p>
        : <StockTable stocks={stocks} />
      }
    </Layout>
  )
}
