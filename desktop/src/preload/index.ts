import { contextBridge, ipcRenderer } from 'electron'

export type ApiStatus = {
  ready: boolean
  baseUrl: string
  error: string
}

contextBridge.exposeInMainWorld('lotteryDesktop', {
  getApiStatus: (): Promise<ApiStatus> => ipcRenderer.invoke('get-api-status'),
  onApiStatus: (cb: (status: ApiStatus) => void) => {
    const listener = (_: unknown, status: ApiStatus) => cb(status)
    ipcRenderer.on('api-status', listener)
    return () => ipcRenderer.removeListener('api-status', listener)
  }
})
