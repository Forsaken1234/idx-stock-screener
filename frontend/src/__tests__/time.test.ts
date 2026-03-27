import { describe, it, expect, vi } from 'vitest'
import { isMarketOpen, isDataStale, formatWIBTime } from '../utils/time'

describe('isMarketOpen', () => {
  it('returns false on weekend', () => {
    vi.useFakeTimers()
    // Saturday UTC = Saturday WIB
    vi.setSystemTime(new Date('2026-03-28T10:00:00Z')) // Saturday
    expect(isMarketOpen()).toBe(false)
    vi.useRealTimers()
  })

  it('returns true during market hours on a weekday', () => {
    vi.useFakeTimers()
    // Monday 10:00 WIB = Monday 03:00 UTC
    vi.setSystemTime(new Date('2026-03-30T03:00:00Z'))
    expect(isMarketOpen()).toBe(true)
    vi.useRealTimers()
  })

  it('returns false before market open', () => {
    vi.useFakeTimers()
    // Monday 08:00 WIB = Monday 01:00 UTC
    vi.setSystemTime(new Date('2026-03-30T01:00:00Z'))
    expect(isMarketOpen()).toBe(false)
    vi.useRealTimers()
  })
})

describe('isDataStale', () => {
  it('returns true when fetched_at is 11 minutes ago', () => {
    const elevenMinAgo = new Date(Date.now() - 11 * 60 * 1000).toISOString()
    expect(isDataStale(elevenMinAgo)).toBe(true)
  })

  it('returns false when fetched_at is 5 minutes ago', () => {
    const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
    expect(isDataStale(fiveMinAgo)).toBe(false)
  })

  it('returns false for null', () => {
    expect(isDataStale(null)).toBe(false)
  })
})
