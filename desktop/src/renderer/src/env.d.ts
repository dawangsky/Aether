/// <reference types="vite/client" />

type ApiStatus = { ready: boolean; baseUrl: string; error: string }

interface LotteryDesktopBridge {
  getApiStatus: () => Promise<ApiStatus>
  onApiStatus: (cb: (status: ApiStatus) => void) => () => void
}

interface Window {
  lotteryDesktop?: LotteryDesktopBridge
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
