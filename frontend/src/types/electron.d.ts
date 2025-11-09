interface ElectronAPI {
  getAppInfo: () => Promise<{ version: string; name: string; appPath: string }>
  send: (channel: string, data: unknown) => void
  receive: (channel: string, func: (...args: any[]) => void) => void
  selectDirectory: (
    options?: {
      title?: string
      defaultPath?: string
      buttonLabel?: string
      properties?: Array<
        | 'openFile'
        | 'openDirectory'
        | 'multiSelections'
        | 'showHiddenFiles'
        | 'createDirectory'
        | 'promptToCreate'
        | 'noResolveAliases'
        | 'treatPackageAsDirectory'
        | 'dontAddToRecent'
      >
    }
  ) => Promise<string | null>
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
