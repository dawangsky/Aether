import { app, BrowserWindow, ipcMain, nativeImage } from 'electron'
import { ChildProcessWithoutNullStreams, spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
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

function resolveAppIconPath(): string | undefined {
  const candidates = [
    join(__dirname, '../../build/icon.icns'),
    join(__dirname, '../../build/icon.png'),
    join(app.getAppPath(), 'build/icon.icns'),
    join(process.resourcesPath || '', 'icon.icns')
  ]
  return candidates.find((p) => p && existsSync(p))
}

function resolveAppIcon() {
  const p = resolveAppIconPath()
  if (!p) return undefined
  const img = nativeImage.createFromPath(p)
  return img.isEmpty() ? undefined : img
}

function projectRoot(): string {
  const fromEnv = process.env.LOTTERY_ROOT
  if (fromEnv && existsSync(join(fromEnv, 'lottery'))) {
    return fromEnv
  }

  if (!app.isPackaged) {
    // out/main -> desktop -> lottery repo
    return join(__dirname, '../../..')
  }

  const candidates = [
    join(homedir(), 'agent', 'lottery'),
    '/Users/wangda/agent/lottery'
  ]
  for (const c of candidates) {
    if (existsSync(join(c, 'lottery', 'api'))) {
      return c
    }
  }
  return candidates[0]
}

function resolvePython(): string {
  const envPython = process.env.LOTTERY_PYTHON
  if (envPython && existsSync(envPython)) return envPython
  const venvPy = join(projectRoot(), '.venv', 'bin', 'python')
  if (existsSync(venvPy)) return venvPy
  return process.platform === 'win32' ? 'python' : 'python3'
}

async function waitForHealth(timeoutMs = 20000): Promise<boolean> {
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
  if (await waitForHealth(1500)) {
    apiReady = true
    mainWindow?.webContents.send('api-status', { ready: true, baseUrl: API_BASE, error: '' })
    return
  }

  if (apiProcess) return
  const python = resolvePython()
  const cwd = projectRoot()
  apiReady = false
  apiProcess = spawn(python, ['-m', 'lottery.api', '--host', '127.0.0.1', '--port', String(DEFAULT_PORT)], {
    cwd,
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  })

  apiProcess.stderr.on('data', (buf) => {
    const text = buf.toString()
    if (text.toLowerCase().includes('error') || text.toLowerCase().includes('address already in use')) {
      apiError = text.slice(0, 500)
    }
  })
  apiProcess.on('exit', (code) => {
    if (!apiReady) {
      apiError = apiError || `API 进程退出，code=${code}`
    }
    apiProcess = null
    apiReady = false
  })

  const ok = await waitForHealth()
  apiReady = ok
  if (!ok) {
    apiError =
      apiError ||
      `无法连接 ${API_BASE}/health。可先手动运行: python -m lottery.api，或设置 LOTTERY_ROOT / LOTTERY_PYTHON`
  }
  mainWindow?.webContents.send('api-status', { ready: apiReady, baseUrl: API_BASE, error: apiError })
}

function stopApi(): void {
  if (!apiProcess) return
  apiProcess.kill('SIGTERM')
  apiProcess = null
  apiReady = false
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
  stopApi()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  stopApi()
})
