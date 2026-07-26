import { app, BrowserWindow, ipcMain, nativeImage } from 'electron'
import { ChildProcessWithoutNullStreams, spawn } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

const DEFAULT_PORT = 8765
const API_BASE = `http://127.0.0.1:${DEFAULT_PORT}`

let mainWindow: BrowserWindow | null = null
let apiProcess: ChildProcessWithoutNullStreams | null = null
let apiReady = false
let apiError = ''
let quitting = false

function emitStatus(extra?: Partial<{ ready: boolean; error: string }>) {
  if (quitting || !mainWindow || mainWindow.isDestroyed()) return
  try {
    mainWindow.webContents.send('api-status', {
      ready: extra?.ready ?? apiReady,
      baseUrl: API_BASE,
      error: extra?.error ?? apiError
    })
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
    emitStatus()
  })
  apiProcess.stderr?.on('data', (buf) => {
    const text = buf.toString()
    if (/error|exception|traceback|address already in use/i.test(text)) {
      apiError = text.slice(0, 600)
    }
  })
  apiProcess.on('exit', (code) => {
    if (!apiReady) {
      apiError = apiError || `API 进程退出，code=${code}`
      emitStatus()
    }
    apiProcess = null
    apiReady = false
  })

  const ok = await waitForHealth()
  apiReady = ok
  apiError = ok
    ? ''
    : apiError || `无法连接 ${API_BASE}/health。请重启应用；若仍失败请反馈日志。`
  emitStatus()
}

function stopApi(): void {
  if (!apiProcess) return
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

  ipcMain.handle('get-api-status', () => ({
    ready: apiReady,
    baseUrl: API_BASE,
    error: apiError
  }))

  createWindow()
  void startApi()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  quitting = true
  stopApi()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  quitting = true
  stopApi()
})
