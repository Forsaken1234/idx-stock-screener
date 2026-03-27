import { NavLink } from 'react-router-dom'
import { isMarketOpen, formatWIBTime } from '../utils/time'

interface SidebarProps {
  lastFetchedAt?: string | null
}

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/screener', label: 'Screener' },
  { to: '/watchlist', label: 'Watchlist' },
]

export default function Sidebar({ lastFetchedAt }: SidebarProps) {
  const open = isMarketOpen()
  return (
    <aside className="w-52 bg-slate-900 flex flex-col shrink-0">
      <div className="p-5 border-b border-slate-800">
        <h1 className="text-indigo-400 font-bold text-lg leading-tight">IDX<br/>Screener</h1>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }: { isActive: boolean }) =>
              `block px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white font-medium'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-800 space-y-2">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${open ? 'bg-emerald-400' : 'bg-slate-500'}`} />
          <span className="text-xs text-slate-400">{open ? 'Market Open' : 'Market Closed'}</span>
        </div>
        {lastFetchedAt && (
          <p className="text-xs text-slate-500">
            Updated {formatWIBTime(lastFetchedAt)}
          </p>
        )}
      </div>
    </aside>
  )
}
