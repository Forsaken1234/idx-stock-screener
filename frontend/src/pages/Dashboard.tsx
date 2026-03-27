import { useMarket } from '../api/market'
import { useStocks } from '../api/stocks'
import MetricCard from '../components/MetricCard'
import Chart from '../components/Chart'
import Layout from '../components/Layout'

export default function Dashboard() {
  const { data: market } = useMarket()
  const { data: stocks = [] } = useStocks()

  const gainers = stocks.filter(s => s.change_pct > 0).length
  const losers = stocks.filter(s => s.change_pct < 0).length
  const oversold = stocks.filter(s => s.rsi != null && s.rsi < 30).length
  const lastFetchedAt = stocks[0]?.fetched_at ?? null

  const topMovers = [...stocks]
    .filter(s => s.change_pct != null)
    .sort((a, b) => Math.abs(b.change_pct) - Math.abs(a.change_pct))
    .slice(0, 5)

  return (
    <Layout lastFetchedAt={lastFetchedAt}>
      <h2 className="text-xl font-semibold mb-6">Dashboard</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="IHSG"
          value={market?.ihsg_price?.toLocaleString('id-ID')}
          sub={market?.ihsg_change_pct != null
            ? `${market.ihsg_change_pct > 0 ? '+' : ''}${market.ihsg_change_pct.toFixed(2)}%`
            : undefined}
          color={market?.ihsg_change_pct != null && market.ihsg_change_pct > 0 ? 'text-emerald-400' : 'text-red-400'}
        />
        <MetricCard label="Gainers" value={gainers} color="text-emerald-400" />
        <MetricCard label="Losers" value={losers} color="text-red-400" />
        <MetricCard label="Oversold (RSI<30)" value={oversold} color="text-amber-400" />
      </div>

      <div className="bg-slate-900 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-medium text-slate-400 mb-3">IHSG Today</h3>
        <Chart data={market?.history ?? []} type="line" height={220} />
      </div>

      <div className="bg-slate-900 rounded-lg p-4">
        <h3 className="text-sm font-medium text-slate-400 mb-3">Top Movers</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-500 border-b border-slate-800">
              <th className="text-left pb-2">Ticker</th>
              <th className="text-left pb-2">Price</th>
              <th className="text-left pb-2">Chg%</th>
            </tr>
          </thead>
          <tbody>
            {topMovers.map(s => (
              <tr key={s.ticker} className="border-b border-slate-800 last:border-0">
                <td className="py-2 text-indigo-400 font-medium">{s.ticker}</td>
                <td className="py-2">{s.price?.toLocaleString('id-ID')}</td>
                <td className={`py-2 ${s.change_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {s.change_pct > 0 ? '+' : ''}{s.change_pct?.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
