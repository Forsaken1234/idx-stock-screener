import { Link } from 'react-router-dom'
import { useWatchlist, useRemoveFromWatchlist } from '../api/watchlist'
import { useStocks } from '../api/stocks'
import Layout from '../components/Layout'

export default function Watchlist() {
  const { data: tickers = [] } = useWatchlist()
  const { data: allStocks = [] } = useStocks()
  const remove = useRemoveFromWatchlist()

  const watchlistStocks = allStocks.filter(s => tickers.includes(s.ticker))
  const lastFetchedAt = watchlistStocks[0]?.fetched_at ?? null

  return (
    <Layout lastFetchedAt={lastFetchedAt}>
      <h2 className="text-xl font-semibold mb-6">Watchlist</h2>

      {tickers.length === 0 ? (
        <p className="text-slate-400">
          Your watchlist is empty. Add stocks from the <Link to="/screener" className="text-indigo-400 underline">Screener</Link> or stock detail pages.
        </p>
      ) : (
        <div className="bg-slate-900 rounded-lg border border-slate-800 divide-y divide-slate-800">
          {watchlistStocks.map(stock => (
            <div key={stock.ticker} className="flex items-center justify-between px-5 py-3">
              <div>
                <Link to={`/stocks/${stock.ticker}`} className="text-indigo-400 font-medium hover:text-indigo-300">
                  {stock.ticker}
                </Link>
                <span className="ml-3 text-slate-300">{stock.price?.toLocaleString('id-ID')}</span>
                <span className={`ml-2 text-sm ${stock.change_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {stock.change_pct > 0 ? '+' : ''}{stock.change_pct?.toFixed(2)}%
                </span>
              </div>
              <div className="flex items-center gap-6 text-sm text-slate-400">
                <span>PE {stock.pe?.toFixed(1) ?? '—'}</span>
                <span>RSI {stock.rsi?.toFixed(1) ?? '—'}</span>
                <button
                  onClick={() => remove.mutate(stock.ticker)}
                  className="text-slate-500 hover:text-red-400 transition-colors"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}
