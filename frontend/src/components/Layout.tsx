import Sidebar from './Sidebar'
import StaleWarning from './StaleWarning'

interface LayoutProps {
  children: React.ReactNode
  lastFetchedAt?: string | null
}

export default function Layout({ children, lastFetchedAt }: LayoutProps) {
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      <Sidebar lastFetchedAt={lastFetchedAt} />
      <div className="flex-1 flex flex-col overflow-auto">
        <StaleWarning fetchedAt={lastFetchedAt} />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
