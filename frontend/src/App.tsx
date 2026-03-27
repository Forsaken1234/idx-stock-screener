import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Screener from './pages/Screener'
import Watchlist from './pages/Watchlist'
import StockDetail from './pages/StockDetail'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/screener" element={<Screener />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/stocks/:ticker" element={<StockDetail />} />
      </Routes>
    </BrowserRouter>
  )
}
