import { Outlet } from 'react-router-dom'
import { useStore } from '../../store'
import Sidebar from './Sidebar'
import Header from './Header'
import { useMarketWS } from '../../lib/websocket'

export default function Layout() {
  const sidebarOpen = useStore(s => s.sidebarOpen)
  useMarketWS() // Start WebSocket connection globally

  return (
    <div className="flex h-screen overflow-hidden bg-bg">
      <Sidebar />
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
        <Header />
        <main className="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
