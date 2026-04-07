import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:       '#0b0c0f',
        surface:  '#111318',
        's2':     '#161820',
        's3':     '#1c1e28',
        border:   '#252730',
        'border-l':'#2f3140',
        tx:       '#e2e4f0',
        'tx-m':   '#7880a0',
        'tx-f':   '#454860',
        primary:  '#00d4aa',
        'pr-d':   '#00a87f',
        gain:     '#22d98a',
        'gain-d': '#15a864',
        loss:     '#ff4d6d',
        'loss-d': '#cc2a48',
        warn:     '#ffb140',
        blue:     '#5b9cf6',
        gold:     '#ffd166',
      },
      fontFamily: {
        sans:  ['Inter', 'system-ui', 'sans-serif'],
        mono:  ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': '0.65rem',
      },
    },
  },
  plugins: [],
} satisfies Config
