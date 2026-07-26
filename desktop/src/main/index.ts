import { app, BrowserWindow, ipcMain, nativeImage } from 'electron'
import { ChildProcessWithoutNullStreams, spawn, spawnSync } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

const DEFAULT_PORT = 8765
const API_BASE = `http://127.0.0.1:${DEFAULT_PORT}`

let mainWindow: BrowserWindow | null = null
let apiProcess: ChildProcessWithoutNullStreams | null = null
let apiReady = false
let apiError = ''

function emitStatus(extra?: Partial<{ ready: boolean; error: string }>) {
  const payload = {
    ready: extra?.ready ?? apiReady,
    baseUrl: API_BASE,
    error: extra?.error ?? apiError
  }
  mainWindow?.webContents.send('api-status', payload)
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

function projectRoot(): string {
  const fromEnv = process.env.LOTTERY_ROOT
  if (fromEnv && existsSync(join(fromEnv, 'lottery'))) {
    return fromEnv
  }

  if (app.isPackaged) {
    const bundled = join(process.resourcesPath, 'backend')
    if (existsSync(join(bundled, 'lottery'))) {
      return bundled
    }
  } else {
    return join(__dirname, '../../..')
  }

  const candidates = [join(homedir(), 'agent', 'lottery'), '/Users/wangda/agent/lottery']
  for (const c of candidates) {
    if (existsSync(join(c, 'lottery', 'api'))) return c
  }
  return candidates[0]
}

function runtimeDirs() {
  const root = join(app.getPath('userData'), 'runtime')
  return {
    root,
    venv: join(root, 'venv'),
    data: join(root, 'data'),
    marker: join(root, 'deps.ok')
  }
}

function listBasePythons(): string[] {
  const envPython = process.env.LOTTERY_PYTHON
  const out: string[] = []
  if (envPython) out.push(envPython)

  if (process.platform === 'win32') {
    out.push('py', 'python', 'python3')
  } else {
    out.push(
      '/opt/homebrew/bin/python3',
      '/usr/local/bin/python3',
      '/Library/Frameworks/Python.framework/Versions/3.12/bin/python3',
      '/Library/Frameworks/Python.framework/Versions/3.11/bin/python3',
      '/Library/Frameworks/Python.framework/Versions/3.10/bin/python3',
      '/usr/bin/python3',
      'python3',
      'python'
    )
  }

  const root = projectRoot()
  if (process.platform === 'win32') {
    out.unshift(join(root, '.venv', 'Scripts', 'python.exe'))
  } else {
    out.unshift(join(root, '.venv', 'bin', 'python3'), join(root, '.venv', 'bin', 'python'))
  }
  return out
}

function pythonVersionOk(bin: string): boolean {
  try {
    const r = spawnSync(bin, ['-c', 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'], {
      encoding: 'utf8',
      timeout: 8000
    })
    return r.status === 0
  } catch {
    return false
  }
}

function resolveBasePython(): string {
  for (const bin of listBasePythons()) {
    if (!bin) continue
    if (bin.includes('/') || bin.includes('\\')) {
      if (!existsSync(bin)) continue
    }
    if (pythonVersionOk(bin)) return bin
  }
  throw new Error('未找到 Python 3.10+。请先安装 Python，然后重新打开 Aether。')
}

function venvPython(venvDir: string): string {
  return process.platform === 'win32'
    ? join(venvDir, 'Scripts', 'python.exe')
    : join(venvDir, 'bin', 'python')
}

function run(bin: string, args: string[], opts?: { cwd?: string; env?: NodeJS.ProcessEnv }): void {
  const r = spawnSync(bin, args, {
    cwd: opts?.cwd,
    env: opts?.env ?? process.env,
    encoding: 'utf8',
    timeout: 1000 * 60 * 8
  })
  if (r.status !== 0) {
    const detail = (r.stderr || r.stdout || '').trim().slice(-800)
    throw new Error(`命令失败: ${bin} ${args.join(' ')}\n${detail}`)
  }
}

function seedData(dataDir: string) {
  mkdirSync(dataDir, { recursive: true })
  const bundledData = join(projectRoot(), 'data')
  for (const name of ['ssq.csv', 'dlt.csv']) {
    const target = join(dataDir, name)
    if (existsSync(target)) continue
    const src = join(bundledData, name)
    if (existsSync(src)) copyFileSync(src, target)
  }
}

async function ensureRuntime(): Promise<string> {
  const dirs = runtimeDirs()
  mkdirSync(dirs.root, { recursive: true })
  seedData(dirs.data)

  const py = venvPython(dirs.venv)
  const req = join(projectRoot(), 'requirements.txt')
  const needInstall = !existsSync(py) || !existsSync(dirs.marker)

  if (!existsSync(py)) {
    emitStatus({ ready: false, error: '正在创建 Python 运行环境…' })
    const base = resolveBasePython()
    run(base, ['-m', 'venv', dirs.venv])
  }

  if (needInstall) {
    emitStatus({ ready: false, error: '正在安装 API 依赖（首次启动较慢）…' })
    const pipPy = venvPython(dirs.venv)
    run(pipPy, ['-m', 'pip', 'install', '--upgrade', 'pip'], { cwd: dirs.root })
    run(pipPy, ['-m', 'pip', 'install', '-r', req], { cwd: dirs.root })
    // sanity import
    run(pipPy, ['-c', 'import fastapi, uvicorn, pydantic, requests, pandas'])
    writeFileSync(dirs.marker, new Date().toISOString())
  }

  return venvPython(dirs.venv)
}

async function waitForHealth(timeoutMs = 30000): Promise<boolean> {
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

  if (await waitForHealth(1200)) {
    apiReady = true
    apiError = ''
    emitStatus()
    return
  }

  if (apiProcess) return

  try {
    const python = app.isPackaged ? await ensureRuntime() : resolveBasePython()
    const cwd = projectRoot()
    const dataDir = app.isPackaged ? runtimeDirs().data : join(cwd, 'data')
    if (!app.isPackaged) seedData(dataDir)

    apiReady = false
    apiProcess = spawn(python, ['-m', 'lottery.api', '--host', '127.0.0.1', '--port', String(DEFAULT_PORT)], {
      cwd,
      env: {
        ...process.env,
        PATH: [
          dirname(python),
          '/opt/homebrew/bin',
          '/usr/local/bin',
          process.env.PATH || '',
          '/usr/bin',
          '/bin'
        ].join(process.platform === 'win32' ? ';' : ':'),
        PYTHONUNBUFFERED: '1',
        PYTHONPATH: [cwd, process.env.PYTHONPATH || ''].filter(Boolean).join(process.platform === 'win32' ? ';' : ':'),
        LOTTERY_DATA_DIR: dataDir
      }
    })

    apiProcess.on('error', (err) => {
      apiError = `启动 API 失败: ${err.message}`
      apiReady = false
      emitStatus()
    })

    apiProcess.stderr.on('data', (buf) => {
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

    const ok = await waitForHealth(45000)
    apiReady = ok
    if (!ok) {
      apiError =
        apiError ||
        `无法连接 ${API_BASE}/health。请安装 Python 3.10+ 后重开应用，或查看是否被防火墙拦截。`
    } else {
      apiError = ''
    }
    emitStatus()
  } catch (e) {
    apiReady = false
    apiError = e instanceof Error ? e.message : String(e)
    emitStatus()
  }
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
