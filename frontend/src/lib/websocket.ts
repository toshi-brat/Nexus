import { useEffect, useRef, useCallback } from 'react'
import { useStore } from '../store'

export function useMarketWS() {
  const ws = useRef<WebSocket | null>(null)
  const setIndices = useStore(s => s.setIndices)

  const connect = useCallback(() => {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    ws.current = new WebSocket(`${proto}://${window.location.host}/ws/market`)
    ws.current.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'indices') setIndices(msg.data)
      } catch { /* ignore */ }
    }
    ws.current.onclose = () => setTimeout(connect, 3000)
    ws.current.onerror = () => ws.current?.close()
  }, [setIndices])

  useEffect(() => {
    connect()
    return () => ws.current?.close()
  }, [connect])
}
