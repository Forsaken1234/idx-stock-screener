import { useEffect, useRef } from 'react'
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts'

interface ChartProps {
  data?: any[]
  type?: 'line' | 'candlestick'
  height?: number
}

export default function Chart({ data = [], type = 'line', height = 300 }: ChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Line'> | ISeriesApi<'Candlestick'> | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const chart = createChart(containerRef.current, {
      height,
      layout: { background: { color: '#0f172a' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
      timeScale: { timeVisible: true },
    })
    chartRef.current = chart

    if (type === 'candlestick') {
      seriesRef.current = chart.addCandlestickSeries({
        upColor: '#10b981', downColor: '#ef4444',
        borderUpColor: '#10b981', borderDownColor: '#ef4444',
        wickUpColor: '#10b981', wickDownColor: '#ef4444',
      })
    } else {
      seriesRef.current = chart.addLineSeries({ color: '#6366f1', lineWidth: 2 })
    }

    return () => chart.remove()
  }, [type, height])

  useEffect(() => {
    if (!seriesRef.current || !data.length) return
    if (type === 'candlestick') {
      (seriesRef.current as ISeriesApi<'Candlestick'>).setData(data.map(d => ({
        time: d.datetime.substring(0, 19) as any,
        open: d.open, high: d.high, low: d.low, close: d.close,
      })))
    } else {
      (seriesRef.current as ISeriesApi<'Line'>).setData(data.map(d => ({
        time: d.datetime.substring(0, 19) as any,
        value: d.close,
      })))
    }
    chartRef.current?.timeScale().fitContent()
  }, [data, type])

  return <div ref={containerRef} className="w-full" />
}
