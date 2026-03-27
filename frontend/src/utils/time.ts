const WIB_OFFSET = 7 * 60 // UTC+7 in minutes

export function toWIB(date: Date = new Date()): Date {
  const utc = date.getTime() + date.getTimezoneOffset() * 60000
  return new Date(utc + WIB_OFFSET * 60000)
}

export function isMarketOpen(): boolean {
  const now = toWIB()
  const day = now.getDay() // 0=Sun, 6=Sat
  if (day === 0 || day === 6) return false
  const hours = now.getHours()
  const minutes = now.getMinutes()
  const total = hours * 60 + minutes
  return total >= 9 * 60 && total <= 15 * 60 + 30
}

export function formatWIBTime(isoString: string | null | undefined): string {
  if (!isoString) return '—'
  const date = new Date(isoString)
  const wib = toWIB(date)
  return wib.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
}

export function isDataStale(fetchedAt: string | null | undefined, thresholdMinutes = 10): boolean {
  if (!fetchedAt) return false
  const diff = (Date.now() - new Date(fetchedAt).getTime()) / 60000
  return diff > thresholdMinutes
}
