import { isDataStale, formatWIBTime } from '../utils/time'

interface StaleWarningProps {
  fetchedAt?: string | null
}

export default function StaleWarning({ fetchedAt }: StaleWarningProps) {
  if (!isDataStale(fetchedAt)) return null
  return (
    <div className="bg-amber-900/50 border-b border-amber-700 px-6 py-2 text-amber-300 text-sm">
      Data may be stale — last updated at {formatWIBTime(fetchedAt)}
    </div>
  )
}
