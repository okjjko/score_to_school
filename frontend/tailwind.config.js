/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: 'var(--c-canvas)',
        'surface-soft': 'var(--c-surface-soft)',
        'surface-card': 'var(--c-surface-card)',
        'surface-cream-strong': 'var(--c-surface-cream-strong)',
        'surface-dark': 'var(--c-surface-dark)',
        'surface-dark-elevated': 'var(--c-surface-dark-elevated)',
        'surface-dark-soft': 'var(--c-surface-dark-soft)',
        ink: 'var(--c-ink)',
        body: 'var(--c-body)',
        'body-strong': 'var(--c-body-strong)',
        muted: 'var(--c-muted)',
        'muted-soft': 'var(--c-muted-soft)',
        hairline: 'var(--c-hairline)',
        'hairline-soft': 'var(--c-hairline-soft)',
        primary: 'var(--c-primary)',
        'primary-active': 'var(--c-primary-active)',
        'primary-disabled': 'var(--c-primary-disabled)',
        'on-primary': 'var(--c-on-primary)',
        'on-dark': 'var(--c-on-dark)',
        'on-dark-soft': 'var(--c-on-dark-soft)',
        success: 'var(--c-success)',
        warning: 'var(--c-warning)',
        error: 'var(--c-error)',
        teal: 'var(--c-teal)',
        amber: 'var(--c-amber)',
      },
      borderRadius: {
        control: '8px',
        card: '12px',
        hero: '16px',
      },
      boxShadow: {
        soft: '0 1px 3px rgba(20,20,19,0.08)',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', '"Noto Serif SC"', '"Songti SC"', '"STSong"', '"SimSun"', '"Times New Roman"', 'Georgia', 'serif'],
        sans: ['Inter', '"Noto Sans SC"', '"PingFang SC"', '"Microsoft YaHei"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
