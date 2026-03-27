interface MetricCardProps {
  label: string
  value?: string | number | null
  sub?: string
  color?: string
}

export default function MetricCard({ label, value, sub, color = 'text-white' }: MetricCardProps) {
  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <p className="text-xs text-slate-400 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-xl font-bold ${color}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}
