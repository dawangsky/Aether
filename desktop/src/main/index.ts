import {
  app,
  BrowserWindow,
  ipcMain,
  Menu,
  nativeImage,
  Tray
} from 'electron'
import { ChildProcessWithoutNullStreams, spawn } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

const DEFAULT_PORT = 8765
const API_BASE = `http://127.0.0.1:${DEFAULT_PORT}`

type CloseAction = 'tray' | 'quit'
type ClosePreference = 'ask' | CloseAction

let mainWindow: BrowserWindow | null = null
let tray: Tray | null = null
let apiProcess: ChildProcessWithoutNullStreams | null = null
let apiReady = false
let apiError = ''
let quitting = false
let startInFlight: Promise<void> | null = null
let closePromptPending = false

function statusPayload(extra?: Partial<{ ready: boolean; error: string }>) {
  return {
    ready: extra?.ready ?? apiReady,
    baseUrl: API_BASE,
    error: extra?.error ?? apiError
  }
}

function emitStatus(extra?: Partial<{ ready: boolean; error: string }>) {
  if (quitting || !mainWindow || mainWindow.isDestroyed()) return
  try {
    mainWindow.webContents.send('api-status', statusPayload(extra))
  } catch {
    // window may be tearing down
  }
}

function resolveAppIconPath(): string | undefined {
  const candidates = [
    join(process.resourcesPath || '', 'icon.icns'),
    join(process.resourcesPath || '', 'icon.ico'),
    join(process.resourcesPath || '', 'icon.png'),
    join(__dirname, '../../build/icon.icns'),
    join(__dirname, '../../build/icon.ico'),
    join(__dirname, '../../build/icon.png')
  ]
  return candidates.find((p) => p && existsSync(p))
}

function resolveAppIcon() {
  const p = resolveAppIconPath()
  if (!p) return undefined
  const img = nativeImage.createFromPath(p)
  return img.isEmpty() ? undefined : img
}

function trayIcon() {
  const img = resolveAppIcon()
  if (img) {
    const size = process.platform === 'darwin' ? 18 : 16
    return img.resize({ width: size, height: size })
  }
  return nativeImage.createEmpty()
}

function prefsPath() {
  return join(app.getPath('userData'), 'window-prefs.json')
}

function loadClosePreference(): ClosePreference {
  try {
    const raw = JSON.parse(readFileSync(prefsPath(), 'utf8')) as { closeAction?: string }
    if (raw.closeAction === 'tray' || raw.closeAction === 'quit' || raw.closeAction === 'ask') {
      return raw.closeAction
    }
  } catch {
    // first run / corrupt
  }
  return 'ask'
}

function saveClosePreference(action: ClosePreference) {
  try {
    writeFileSync(prefsPath(), JSON.stringify({ closeAction: action }, null, 2), 'utf8')
  } catch {
    // ignore persistence errors
  }
}

function dataDir(): string {
  return join(app.getPath('userData'), 'runtime', 'data')
}

function seedDataDir(): string | null {
  const candidates = [
    join(process.resourcesPath || '', 'backend', 'data'),
    join(__dirname, '../../../data'),
    join(homedir(), 'agent', 'lottery', 'data')
  ]
  return candidates.find((p) => p && existsSync(p)) || null
}

function ensureData() {
  const dest = dataDir()
  mkdirSync(dest, { recursive: true })
  const srcRoot = seedDataDir()
  if (!srcRoot) return
  for (const name of ['ssq.csv', 'dlt.csv']) {
    const target = join(dest, name)
    if (existsSync(target)) continue
    const src = join(srcRoot, name)
    if (existsSync(src)) copyFileSync(src, target)
  }
}

function resolveBundledApi(): string | null {
  const name = process.platform === 'win32' ? 'aether-api.exe' : 'aether-api'
  const candidates = [
    join(process.resourcesPath || '', 'bin', name),
    join(__dirname, '../../resources/bin', name)
  ]
  return candidates.find((p) => p && existsSync(p)) || null
}

function resolveDevPython(): string {
  const root = join(__dirname, '../../..')
  const venv =
    process.platform === 'win32'
      ? join(root, '.venv', 'Scripts', 'python.exe')
      : join(root, '.venv', 'bin', 'python')
  if (existsSync(venv)) return venv
  return process.platform === 'win32' ? 'python' : 'python3'
}

async function waitForHealth(timeoutMs = 45000): Promise<boolean> {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    if (quitting) return false
    try {
      const res = await fetch(`${API_BASE}/health`)
      if (res.ok) return true
    } catch {
      // retry
    }
    await new Promise((r) => setTimeout(r, 400))
  }
  return false
}

async function startApi(): Promise<void> {
  if (startInFlight) return startInFlight
  startInFlight = doStartApi().finally(() => {
    startInFlight = null
  })
  return startInFlight
}

async function doStartApi(): Promise<void> {
  if (quitting) return
  apiError = ''
  emitStatus({ ready: false, error: '正在启动本地 API…' })
  ensureData()

  if (await waitForHealth(1200)) {
    apiReady = true
    apiError = ''
    emitStatus()
    return
  }
  if (apiProcess) return

  const bundled = resolveBundledApi()
  const env = {
    ...process.env,
    PYTHONUNBUFFERED: '1',
    LOTTERY_DATA_DIR: dataDir()
  }

  try {
    if (bundled) {
      apiProcess = spawn(bundled, ['--host', '127.0.0.1', '--port', String(DEFAULT_PORT)], {
        env,
        cwd: dataDir()
      })
    } else if (!app.isPackaged) {
      const root = join(__dirname, '../../..')
      const python = resolveDevPython()
      apiProcess = spawn(python, ['-m', 'lottery.api', '--host', '127.0.0.1', '--port', String(DEFAULT_PORT)], {
        cwd: root,
        env: {
          ...env,
          PYTHONPATH: [root, process.env.PYTHONPATH || ''].filter(Boolean).join(process.platform === 'win32' ? ';' : ':')
        }
      })
    } else {
      throw new Error('安装包缺少内嵌 API（bin/aether-api）。请重新下载完整发行版。')
    }
  } catch (e) {
    apiReady = false
    apiError = e instanceof Error ? e.message : String(e)
    emitStatus()
    return
  }

  apiProcess.on('error', (err) => {
    apiError = `启动 API 失败: ${err.message}`
    apiReady = false
    apiProcess = null
    emitStatus()
  })
  apiProcess.stderr?.on('data', (buf) => {
    const text = buf.toString()
    if (/error|exception|traceback|address already in use/i.test(text)) {
      apiError = text.slice(0, 600)
    }
  })
  apiProcess.on('exit', (code) => {
    apiProcess = null
    apiReady = false
    if (!quitting) {
      apiError = apiError || (code == null ? 'API 已停止' : `API 进程退出，code=${code}`)
      emitStatus()
    }
  })

  const ok = await waitForHealth()
  if (quitting) return
  apiReady = ok
  apiError = ok
    ? ''
    : apiError || `无法连接 ${API_BASE}/health。可点击右上角「启动」重试。`
  emitStatus()
}

function stopApi(manual = false): void {
  if (!apiProcess) {
    apiReady = false
    if (manual) {
      apiError = 'API 已关闭'
      emitStatus()
    }
    return
  }
  const proc = apiProcess
  apiProcess = null
  apiReady = false
  proc.removeAllListeners('exit')
  proc.removeAllListeners('error')
  try {
    proc.kill('SIGTERM')
  } catch {
    // already exiting
  }
  if (manual && !quitting) {
    apiError = 'API 已关闭'
    emitStatus()
  }
}

function showMainWindow() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    createWindow()
  } else {
    if (mainWindow.isMinimized()) mainWindow.restore()
    mainWindow.show()
    mainWindow.focus()
  }
  if (!apiReady && !apiProcess) void startApi()
  else emitStatus()
}

function ensureTray() {
  if (tray) return
  const icon = trayIcon()
  tray = new Tray(icon.isEmpty() ? nativeImage.createFromDataURL(
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAFUlEQVQ4T2NkYGD4z0BUYGwYRgYGADv+Ax0Vq0qNAAAAAElFTkSuQmCC'
  ) : icon)
  tray.setToolTip('Aether')
  const menu = Menu.buildFromTemplate([
    {
      label: '显示窗口',
      click: () => showMainWindow()
    },
    { type: 'separator' },
    {
      label: '退出程序',
      click: () => {
        quitting = true
        stopApi()
        app.quit()
      }
    }
  ])
  tray.setContextMenu(menu)
  tray.on('click', () => showMainWindow())
  tray.on('double-click', () => showMainWindow())
}

function hideToTray() {
  ensureTray()
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.hide()
  }
}

function requestClosePrompt() {
  if (!mainWindow || mainWindow.isDestroyed()) return
  if (closePromptPending) return
  closePromptPending = true
  mainWindow.show()
  mainWindow.focus()
  mainWindow.webContents.send('close-prompt')
}

function handleCloseIntent() {
  if (quitting) return
  const pref = loadClosePreference()
  if (pref === 'tray') {
    hideToTray()
    return
  }
  if (pref === 'quit') {
    quitting = true
    stopApi()
    app.quit()
    return
  }
  requestClosePrompt()
}

function createWindow(): void {
  const icon = resolveAppIcon()
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 780,
    minWidth: 960,
    minHeight: 640,
    title: 'Aether',
    ...(icon ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  })

  if (process.env.ELECTRON_RENDERER_URL) {
    void mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    void mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  mainWindow.on('close', (e) => {
    if (quitting) return
    e.preventDefault()
    handleCloseIntent()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(() => {
  app.setName('Aether')
  const iconPath = resolveAppIconPath()
  app.setAboutPanelOptions({
    applicationName: 'Aether',
    version: app.getVersion(),
    copyright: 'Copyright © Aether',
    ...(iconPath ? { iconPath } : {})
  })

  ipcMain.handle('get-api-status', () => statusPayload())
  ipcMain.handle('start-api', async () => {
    await startApi()
    return statusPayload()
  })
  ipcMain.handle('stop-api', async () => {
    stopApi(true)
    await new Promise((r) => setTimeout(r, 300))
    return statusPayload()
  })
  ipcMain.handle(
    'close-decision',
    (_evt, payload: { action: 'tray' | 'quit' | 'cancel'; remember?: boolean }) => {
      closePromptPending = false
      const action = payload?.action
      if ((action === 'tray' || action === 'quit') && payload.remember) {
        saveClosePreference(action)
      }
      if (action === 'tray') {
        hideToTray()
        return { ok: true }
      }
      if (action === 'quit') {
        quitting = true
        stopApi()
        app.quit()
        return { ok: true }
      }
      return { ok: true }
    }
  )
  ipcMain.handle('get-window-prefs', () => ({
    closeAction: loadClosePreference()
  }))
  ipcMain.handle('set-window-prefs', (_evt, payload: { closeAction?: ClosePreference }) => {
    const next = payload?.closeAction
    if (next === 'ask' || next === 'tray' || next === 'quit') {
      saveClosePreference(next)
    }
    return { closeAction: loadClosePreference() }
  })

  createWindow()
  void startApi()

  app.on('activate', () => {
    showMainWindow()
  })
})

app.on('window-all-closed', () => {
  // 托盘后台运行时不退出；macOS 也保持进程。
  if (tray && !quitting) return
  if (process.platform === 'darwin' && !quitting) return
  quitting = true
  stopApi()
  app.quit()
})

app.on('before-quit', () => {
  quitting = true
  stopApi()
  if (tray) {
    tray.destroy()
    tray = null
  }
})
