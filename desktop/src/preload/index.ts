import { contextBridge, ipcRenderer } from 'electron'

export type ApiStatus = {
  ready: boolean
  baseUrl: string
  error: string
}

export type CloseDecision = {
  action: 'tray' | 'quit' | 'cancel'
  remember?: boolean
}

export type ClosePreference = 'ask' | 'tray' | 'quit'

export type WindowPrefs = {
  closeAction: ClosePreference
}

contextBridge.exposeInMainWorld('lotteryDesktop', {
  getApiStatus: (): Promise<ApiStatus> => ipcRenderer.invoke('get-api-status'),
  startApi: (): Promise<ApiStatus> => ipcRenderer.invoke('start-api'),
  stopApi: (): Promise<ApiStatus> => ipcRenderer.invoke('stop-api'),
  onApiStatus: (cb: (status: ApiStatus) => void) => {
    const listener = (_: unknown, status: ApiStatus) => cb(status)
    ipcRenderer.on('api-status', listener)
    return () => ipcRenderer.removeListener('api-status', listener)
  },
  onClosePrompt: (cb: () => void) => {
    const listener = () => cb()
    ipcRenderer.on('close-prompt', listener)
    return () => ipcRenderer.removeListener('close-prompt', listener)
  },
  decideClose: (decision: CloseDecision): Promise<{ ok: boolean }> =>
    ipcRenderer.invoke('close-decision', decision),
  getWindowPrefs: (): Promise<WindowPrefs> => ipcRenderer.invoke('get-window-prefs'),
  setWindowPrefs: (prefs: Partial<WindowPrefs>): Promise<WindowPrefs> =>
    ipcRenderer.invoke('set-window-prefs', prefs)
})
