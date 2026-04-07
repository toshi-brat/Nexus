import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }

export const fmt = {
  price:  (n: number) => n?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '--',
  pct:    (n: number) => (n >= 0 ? '+' : '') + n?.toFixed(2) + '%',
  change: (n: number) => (n >= 0 ? '+' : '') + n?.toFixed(2),
  inr:    (n: number) => '₹' + n?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
  date:   (s: string) => s ? new Date(s).toLocaleDateString('en-IN', { day:'2-digit', month:'short' }) : '--',
  time:   (s: string) => s ? new Date(s).toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' }) : '--',
}

export const colorPnl = (n: number) => n > 0 ? 'gain-text' : n < 0 ? 'loss-text' : 'neutral-text'
