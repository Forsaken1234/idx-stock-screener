import { useState } from 'react'
import { Link } from 'react-router-dom'

interface Stock {
  ticker: string
  price?: number | null
  change_pct?: number | null
  pe?: number | null
  pbv?: number | null
  roe?: number | null
  rsi?: number | null
  market_cap?: number | null
  [key: string]: any
}

interface StockTableProps {
  stocks?: Stock[]
}

const COLUMNS: Array<{
  key: string
  label: string
  fmt?: (v: any) => string
  color?: (v: any) => string
}> = [
  { key: 'ticker', label: 'Ticker' },
  { key: 'price', label: 'Price', fmt: (v: number) => v?.toLocaleString('id-ID') },
  {
    key: 'change_pct', label: 'Chg%',
    fmt: (v: number) => v != null ? `${v > 0 ? '+' : ''}${v.toFixed(2)}%` : '—',
    color: (v: number) => v > 0 ? 'text-emerald-400' : v < 0 ? 'text-red-400' : '',
  },
  { key: 'pe', label: 'PE', fmt: (v: number) => v?.toFixed(1) },
  { key: 'pbv', label: 'PBV', fmt: (v: number) => v?.toFixed(2) },
  { key: 'roe', label: 'ROE%', fmt: (v: number) => v != null ? `${(v * 100).toFixed(1)}%` : '—' },
  {
    key: 'rsi', label: 'RSI',
    fmt: (v: number) => v?.toFixed(1),
    color: (v: number) => v < 30 ? 'text-emerald-400 font-bold' : v > 70 ? 'text-red-400 font-bold' : '',
  },
  { key: 'market_cap', label: 'Mkt Cap', fmt: (v: number) => v != null ? `${(v / 1e12).toFixed(1)}T` : '—' },
]

export default function StockTable({ stocks = [] }: StockTableProps) {
  const [sort, setSort] = useState<{ key: string; dir: 'asc' | 'desc' }>({ key: 'market_cap', dir: 'desc' })

  const sorted = [...stocks].sort((a, b) => {
    const va = a[sort.key], vb = b[sort.key]
    if (va == null) return 1
    if (vb == null) return -1
    return sort.dir === 'asc' ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1)
  })

  const toggleSort = (key: string) => setSort(s => ({
    key, dir: s.key === key && s.dir === 'desc' ? 'asc' : 'desc'
  }))

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800 bg-slate-900">
            {COLUMNS.map(col => (
              <th
                key={col.key}
                onClick={() => toggleSort(col.key)}
                className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wide cursor-pointer hover:text-slate-200 select-none"
              >
                {col.label}
                {sort.key === col.key && (sort.dir === 'asc' ? ' ↑' : ' ↓')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {sorted.map(stock => (
            <tr key={stock.ticker} className="hover:bg-slate-800/50 transition-colors">
              {COLUMNS.map(col => {
                const val = stock[col.key]
                const displayed = col.fmt ? (col.fmt(val) ?? '—') : (val ?? '—')
                const colorClass = col.color ? col.color(val) : ''
                return (
                  <td key={col.key} className={`px-4 py-3 ${colorClass}`}>
                    {col.key === 'ticker'
                      ? <Link to={`/stocks/${val}`} className="text-indigo-400 hover:text-indigo-300 font-medium">{val}</Link>
                      : displayed
                    }
                  </td>
                )
              })}
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td colSpan={COLUMNS.length} className="px-4 py-8 text-center text-slate-500">
                No stocks match your filters
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
