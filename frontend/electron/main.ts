import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { spawn, ChildProcess } from 'child_process'
import { platform } from 'os'

// 是否是开发环境
const isDev = process.env.NODE_ENV === 'development'

// FastAPI进程
let fastApiProcess: ChildProcess | null = null

// 主窗口
let mainWindow: BrowserWindow | null = null

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  })
  //隐藏菜单栏
  mainWindow.setMenu(null);
  // 加载应用
  if (isDev) {
    // 开发环境下，加载Vite开发服务器
    // 由于端口可能会变化，尝试5173和5174
    mainWindow.loadURL('http://localhost:5174').catch(() => {
      mainWindow?.loadURL('http://localhost:5173')
    })
    // 打开开发者工具
    mainWindow.webContents.openDevTools()
  } else {
    // 生产环境下，加载打包后的index.html
    const indexPath = join(__dirname, '..', 'index.html')
    console.log('Loading index from:', indexPath)
    mainWindow.loadFile(indexPath)
  }

  // 窗口关闭时释放引用
  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// 启动FastAPI后端
function startFastApi() {
  console.log('Starting FastAPI backend...')
  
  if (isDev) {
    // 开发模式：使用 Python 脚本启动
    const backendDir = join(__dirname, '..', '..', '..', 'backend')
    const pythonScript = join(backendDir, 'app', 'main.py')
    
    console.log('Development mode: Starting Python script')
    console.log('Backend directory:', backendDir)
    console.log('Python script:', pythonScript)
    
    try {
        // 使用 Python 直接运行 main.py
          fastApiProcess = spawn('python', ['app/main.py'], {
            cwd: backendDir,
            stdio: ['ignore', 'pipe', 'pipe']
          })
      } catch (error) {
        console.error('Failed to start FastAPI in development mode:', error)
      }
  } else {
    // 生产模式：使用打包的 exe 文件
    const backendExecutable = join(process.resourcesPath, 'fastapi-backend.exe')
    
    console.log('Production mode: Starting packaged executable')
    console.log('Executable:', backendExecutable)
    
    try {
      fastApiProcess = spawn(backendExecutable, [], {
        stdio: ['ignore', 'pipe', 'pipe']
      })
    } catch (error) {
      console.error('Failed to start FastAPI in production mode:', error)
    }
  }

  // 处理FastAPI进程的输出
  if (fastApiProcess?.stdout) fastApiProcess.stdout.on('data', (data) => {
    console.log(`FastAPI output: ${data}`)
  })

  if (fastApiProcess?.stderr) fastApiProcess.stderr.on('data', (data) => {
    console.error(`FastAPI error: ${data}`)
  })

  fastApiProcess?.on('close', (code) => {
    console.log(`FastAPI process exited with code ${code}`)
    fastApiProcess = null
  })
}

// 当Electron应用准备好时，创建窗口
app.whenReady().then(() => {
  // 启动FastAPI后端
  startFastApi()
  
  // 创建主窗口
  createWindow()

  // 在macOS上，当所有窗口关闭时，重新创建窗口
  app.on('activate', () => {
    if (mainWindow === null) {
      createWindow()
    }
  })
})

// 当所有窗口关闭时，退出应用
app.on('window-all-closed', () => {
  // 在macOS上，应用和菜单栏通常会保持活动状态，直到用户使用Cmd+Q明确退出
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 应用退出前，关闭FastAPI进程
app.on('before-quit', () => {
  if (fastApiProcess) {
    console.log('关闭FastAPI进程...')
    if (platform() === 'win32') {
      // Windows上使用taskkill强制终止进程
      // 确保进程ID存在后再执行taskkill
      if (fastApiProcess.pid) {
        spawn('taskkill', ['/pid', fastApiProcess.pid.toString(), '/f', '/t'])
      } else {
        console.error('无法获取FastAPI进程ID')
      }
    } else {
      // 其他平台使用kill信号
      fastApiProcess.kill('SIGTERM')
    }
  }
})

// 设置IPC通信
ipcMain.handle('get-app-info', () => {
  return {
    version: app.getVersion(),
    name: app.getName(),
    appPath: app.getAppPath()
  }
})