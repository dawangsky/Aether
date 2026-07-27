/// <reference types="vite/client" />

type ApiStatus = { ready: boolean; baseUrl: string; error: string }

type CloseDecision = {
  action: 'tray' | 'quit' | 'cancel'
  remember?: boolean
}

type ClosePreference = 'ask' | 'tray' | 'quit'

type WindowPrefs = {
  closeAction: ClosePreference
}

interface LotteryDesktopBridge {
  getApiStatus: () => Promise<ApiStatus>
  startApi: () => Promise<ApiStatus>
  stopApi: () => Promise<ApiStatus>
  onApiStatus: (cb: (status: ApiStatus) => void) => () => void
  onClosePrompt: (cb: () => void) => () => void
  decideClose: (decision: CloseDecision) => Promise<{ ok: boolean }>
  getWindowPrefs: () => Promise<WindowPrefs>
  setWindowPrefs: (prefs: Partial<WindowPrefs>) => Promise<WindowPrefs>
}

interface Window {
  lotteryDesktop?: LotteryDesktopBridge
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
