import { NavLink } from 'react-router-dom'
import { Activity, BarChart2, BookOpen, LineChart, PieChart, Target, ChevronLeft, ChevronRight } from 'lucide-react'
import { useStore } from '../../store'

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useStore()

  const links = [
    { to: '/', icon: Activity, label: 'Overview' },
    { to: '/sentiment', icon: BarChart2, label: 'Sentiment' },
    { to: '/portfolio', icon: PieChart, label: 'Portfolio' },
    { to: '/paper', icon: BookOpen, label: 'Paper Trading' },
    { to: '/analysis', icon: LineChart, label: 'Analysis' },
    { to: '/strategy', icon: Target, label: 'Strategy' },
  ]

  return (
    <div className={`fixed inset-y-0 left-0 bg-surface border-r border-border flex flex-col transition-all duration-300 z-20 ${sidebarOpen ? 'w-64' : 'w-16'}`}>
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        {sidebarOpen && <span className="font-mono font-bold tracking-wider text-primary text-lg">NEXUS</span>}
        <button onClick={toggleSidebar} className="p-1 hover:bg-border rounded text-tx-m hover:text-tx transition-colors mx-auto">
          {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      <nav className="flex-1 py-6 px-3 space-y-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors ${
              isActive ? 'bg-primary/10 text-primary' : 'text-tx-m hover:bg-border hover:text-tx'
            }`}
          >
            <link.icon size={20} className="shrink-0" />
            {sidebarOpen && <span className="font-medium text-sm">{link.label}</span>}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
