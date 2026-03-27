import { useParams } from 'react-router-dom'
import { useStock } from '../api/stocks'
import { useWatchlist, useAddToWatchlist, useRemoveFromWatchlist } from '../api/watchlist'
import Chart from '../components/Chart'
import MetricCard from '../components/MetricCard'
import Layout from '../components/Layout'

interface IndicatorProps {
  label: string
  value: string | number | null | undefined
  unit?: string
}

function Indicator({ label, value, unit = '' }: IndicatorProps) {
  return (
    <div className="flex justify-between py-2 border-b border-slate-800 last:border-0">
      <span className="text-slate-400 text-sm">{label}</span>
      <span className="text-slate-100 text-sm font-medium">{value != null ? `${value}${unit}` : '—'}</span>
    </div>
  )
}

export default function StockDetail() {
  const { ticker } = useParams<{ ticker: string }>()
  const { data: stock, isLoading } = useStock(ticker)
  const { data: watchlist = [] } = useWatchlist()
  const add = useAddToWatchlist()
  const remove = useRemoveFromWatchlist()
  const inWatchlist = watchlist.includes(ticker!)

  if (isLoading) return <Layout><p className="text-slate-400">Loading…</p></Layout>
  if (!stock || 'detail' in stock) return <Layout><p className="text-red-400">Stock not found.</p></Layout>

  return (
    <Layout lastFetchedAt={stock.fetched_at}>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">{ticker}</h2>
          <p className="text-slate-400 text-sm">{stock.name} · {stock.sector}</p>
          <p className="text-sm text-slate-500 mt-1">{stock.indices?.join(', ')}</p>
        </div>
        <button
          onClick={() => inWatchlist ? remove.mutate(ticker!) : add.mutate(ticker!)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            inWatchlist
              ? 'bg-slate-700 text-slate-300 hover:bg-red-900 hover:text-red-300'
              : 'bg-indigo-600 text-white hover:bg-indigo-500'
          }`}
        >
          {inWatchlist ? '★ Remove from Watchlist' : '☆ Add to Watchlist'}
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard
          label="Price"
          value={stock.price?.toLocaleString('id-ID')}
          sub={stock.change_pct != null
            ? `${stock.change_pct > 0 ? '+' : ''}${stock.change_pct.toFixed(2)}%`
            : undefined}
          color={stock.change_pct > 0 ? 'text-emerald-400' : 'text-red-400'}
        />
        <MetricCard label="Market Cap" value={stock.market_cap ? `${(stock.market_cap / 1e12).toFixed(1)}T` : '—'} />
        <MetricCard label="RSI (14)" value={stock.rsi?.toFixed(1)}
          color={stock.rsi < 30 ? 'text-emerald-400' : stock.rsi > 70 ? 'text-red-400' : 'text-white'} />
      </div>

      <div className="bg-slate-900 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-medium text-slate-400 mb-3">Price Chart (Today)</h3>
        <Chart data={stock.price_history ?? []} type="candlestick" height={280} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-900 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Fundamentals</h3>
          <Indicator label="PE Ratio" value={stock.pe?.toFixed(1)} />
          <Indicator label="PBV" value={stock.pbv?.toFixed(2)} />
          <Indicator label="ROE" value={stock.roe != null ? (stock.roe * 100).toFixed(1) : null} unit="%" />
          <Indicator label="EPS" value={stock.eps?.toFixed(0)} />
          <Indicator label="Div Yield" value={stock.div_yield != null ? (stock.div_yield * 100).toFixed(2) : null} unit="%" />
        </div>
        <div className="bg-slate-900 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Technicals</h3>
          <Indicator label="MA (20)" value={stock.ma20?.toLocaleString('id-ID')} />
          <Indicator label="MA (50)" value={stock.ma50?.toLocaleString('id-ID')} />
          <Indicator label="MACD Line" value={stock.macd_line?.toFixed(2)} />
          <Indicator label="MACD Signal" value={stock.macd_signal?.toFixed(2)} />
          <Indicator label="BB Upper" value={stock.bb_upper?.toLocaleString('id-ID')} />
          <Indicator label="BB Lower" value={stock.bb_lower?.toLocaleString('id-ID')} />
        </div>
      </div>
    </Layout>
  )
}
