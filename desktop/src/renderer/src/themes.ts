export type ThemeId = 'terminal' | 'ledger' | 'mist' | 'celadon'

export type ThemeOption = {
  id: ThemeId
  name: string
  tagline: string
  vibe: string
  swatches: string[]
}

export const THEMES: ThemeOption[] = [
  {
    id: 'terminal',
    name: '墨金终端',
    tagline: 'Terminal Gold',
    vibe: '深色交易台 + 弱金点缀，偏 Bloomberg / 夜盘终端',
    swatches: ['#070b10', '#c4a35a', '#2f9e6b', '#c75b5b', '#d7e0ea']
  },
  {
    id: 'ledger',
    name: '研报账本',
    tagline: 'Research Ledger',
    vibe: '浅色研究台 + 海军蓝，像券商研报与对账工作台',
    swatches: ['#f3f5f8', '#1e3a5f', '#0f766e', '#b42318', '#152033']
  },
  {
    id: 'mist',
    name: '云纱白昼',
    tagline: 'Cloud Mist',
    vibe: '浅灰白底 + 天空蓝点缀，清爽白天办公台',
    swatches: ['#f0f3f7', '#3d6f9c', '#2a8a72', '#c44a4a', '#1a2836']
  },
  {
    id: 'celadon',
    name: '青瓷台面',
    tagline: 'Celadon Desk',
    vibe: '淡青瓷色底 + 墨青字，偏瓷器釉面浅色工作台',
    swatches: ['#eef4f0', '#3d5c52', '#2f7a68', '#b54848', '#1e2e28']
  }
]

const STORAGE_KEY = 'lq-terminal-theme'

export function loadTheme(): ThemeId {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw === 'kline' || raw === 'ink') return 'mist'
  if (THEMES.some((t) => t.id === raw)) return raw as ThemeId
  return 'terminal'
}

export function saveTheme(id: ThemeId) {
  localStorage.setItem(STORAGE_KEY, id)
}

export function applyTheme(id: ThemeId) {
  document.documentElement.setAttribute('data-theme', id)
  saveTheme(id)
}
