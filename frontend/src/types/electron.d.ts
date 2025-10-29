interface ElectronAPI {
  getAppInfo: () => Promise<{ version: string; name: string; appPath: string }>
  send: (channel: string, data: unknown) => void
  receive: (channel: string, func: (...args: any[]) => void) => void
}

interface AppRuntimeBackendInfo {
  protocol: string
  host: string
  port: string
  url: string
}

interface AppRuntimeInfo {
  isElectron: boolean
  platform: NodeJS.Platform
  backend: AppRuntimeBackendInfo
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI
    appRuntime?: AppRuntimeInfo
  }
}

export {}
