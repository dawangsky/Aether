import { app, BrowserWindow, ipcMain } from 'electron'
import { ChildProcessWithoutNullStreams, spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

const DEFAULT_PORT = 8765
const API_BASE = `http://127.0.0.1:${DEFAULT_PORT}`

let mainWindow: BrowserWindow | null = null
let apiProcess: ChildProcessWithoutNullStreams | null = null
let apiReady = false
let apiError = ''

function projectRoot(): string {
  // out/main -> desktop -> lottery
  return join(__dirname, '../../..')
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
  // 若已有本地服务（例如手动启动），直接复用
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
    apiError = apiError || `无法连接 ${API_BASE}/health，请检查 .venv 或设置 LOTTERY_PYTHON`
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
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 780,
    minWidth: 960,
    minHeight: 640,
    title: 'LQ Terminal',
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
