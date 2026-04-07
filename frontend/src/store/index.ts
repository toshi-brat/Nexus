import { create } from 'zustand'

interface IndexData { last: number; change: number; pct: number; open: number; high: number; low: number }

interface Store {
  indices: Record<string, IndexData>
  setIndices: (data: Record<string, IndexData>) => void
  sidebarOpen: boolean
  toggleSidebar: () => void
  activePage: string
  setActivePage: (p: string) => void
}

export const useStore = create<Store>((set) => ({
  indices:     {},
  setIndices:  (indices) => set({ indices }),
  sidebarOpen: true,
  toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),
  activePage:  'overview',
  setActivePage: (activePage) => set({ activePage }),
}))
