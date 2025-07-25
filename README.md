# 🚀 Electron + FastAPI + Vue3 桌面应用

一个现代化的桌面应用，结合了Electron、FastAPI和Vue3的强大功能。应用采用PyInstaller打包方案，实现完全独立的可执行文件，无需用户安装Python环境。

## ✨ 特性

- 🖥️ **跨平台桌面应用**：基于Electron构建
- ⚡ **现代前端技术栈**：Vue3 + TypeScript + Pinia + Arco Design
- 🐍 **高性能后端API**：FastAPI + Python
- 📦 **独立打包**：使用PyInstaller，无需Python环境依赖
- 🔄 **热重载开发**：支持前后端热重载
- 🛡️ **类型安全**：全面的TypeScript支持

## 📁 项目结构

```
fastApiProjectByGK/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   └── main.py            # FastAPI应用入口
│   ├── dist/                  # PyInstaller打包输出
│   │   └── fastapi-backend.exe # 独立后端可执行文件
│   ├── pyproject.toml         # Python依赖管理
│   └── uv.lock               # 依赖锁定文件
├── frontend/                  # Electron + Vue3前端
│   ├── electron/              # Electron主进程
│   │   ├── main.ts           # 主进程入口
│   │   └── preload.ts        # 预加载脚本
│   ├── src/                  # Vue3应用源码
│   │   ├── components/       # Vue组件
│   │   ├── views/           # 页面视图
│   │   ├── router/          # 路由配置
│   │   ├── store/           # 状态管理
│   │   └── api/             # API接口
│   ├── resources/           # 资源文件
│   │   └── fastapi-backend.exe # 后端可执行文件
│   ├── release/             # 打包输出
│   │   └── MyElectronApp Setup 1.0.0.exe # 安装包
│   └── package.json         # 前端依赖配置
└── README.md               # 项目说明
```

## 🛠️ 技术栈

### 前端技术
- **Electron** - 跨平台桌面应用框架
- **Vue 3** - 渐进式JavaScript框架
- **TypeScript** - 类型安全的JavaScript超集
- **Pinia** - Vue状态管理库
- **Arco Design** - 企业级UI组件库
- **Vite** - 快速构建工具

### 后端技术
- **FastAPI** - 现代高性能Web框架
- **Python 3.12+** - 编程语言
- **Uvicorn** - ASGI服务器
- **PyInstaller** - Python应用打包工具

### 开发工具
- **uv** - 快速Python包管理器
- **electron-builder** - Electron应用打包工具

## 📋 环境要求

### 开发环境
- **Node.js** 16.0+
- **Python** 3.12+
- **uv** (推荐) 或 pip
- **npm** 或 yarn

### 运行环境
- **Windows** 10/11
- **Mac** 

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd electron-fastapi-starter
```

### 2. 安装后端依赖

```bash
cd backend
# 使用uv (推荐)
uv sync

# 或使用pip
pip install -e .
```

### 3. 安装前端依赖

```bash
cd ../frontend
npm install
```

### 4. 开发模式启动

#### 方式一：一键启动（推荐）
```bash
# 直接启动Electron开发模式（自动启动后端）
cd frontend
npm run electron:dev
```

#### 方式二：分别启动
```bash
# 终端1：手动启动后端（可选）
cd backend
python app/main.py

# 终端2：启动前端
cd frontend
npm run electron:dev
```

#### 🔧 开发模式说明
- **后端端口**：`http://localhost:8001`（开发模式）
- **前端端口**：`http://localhost:5174`（Vite开发服务器）
- **自动启动**：`npm run electron:dev` 会自动启动后端Python脚本
- **热重载**：前端代码修改会自动刷新，后端修改需重启

## 📦 生产环境打包

### 完整打包流程

```bash
# 1. 打包后端为独立exe
cd backend
uv run pyinstaller --onefile --name fastapi-backend app/main.py

# 2. 复制后端exe到前端资源目录
cp dist/fastapi-backend.exe ../frontend/resources/

# 3. 构建前端
cd ../frontend
npm run build

# 4. 打包Electron应用
npm run electron:build
```

### 输出文件
- **安装包**：`frontend/release/MyElectronApp Setup 1.0.0.exe`
- **便携版**：`frontend/release/win-unpacked/MyElectronApp.exe`

## 🔧 开发指南

### 添加Python依赖

```bash
cd backend
# 添加新依赖
uv add package-name

# 重新打包后端
uv run pyinstaller --onefile --name fastapi-backend app/main.py

# 复制到前端并重新打包
cp dist/fastapi-backend.exe ../frontend/resources/
cd ../frontend
npm run build
npm run electron:build
```

### 添加前端依赖

```bash
cd frontend
npm install package-name
```

### API开发

后端API在 `backend/app/main.py` 中定义：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/example")
async def example_endpoint():
    return {"message": "Hello from FastAPI!"}
```

### 前端API调用

在 `frontend/src/api/` 中定义API接口：

```typescript
// api/example.ts
export const getExample = async () => {
  // 开发模式：http://localhost:8001
  // 生产模式：http://localhost:8000
  const response = await fetch('/api/example') // 使用相对路径，自动适配
  return response.json()
}
```

**注意**：项目已配置API代理，使用相对路径即可自动适配开发/生产环境的不同端口。

## 🐛 常见问题

### Q: 开发模式启动时出现端口冲突？
A: 项目已配置开发模式使用8001端口，生产模式使用8000端口。如仍有冲突，可在 `backend/app/main.py` 中修改端口配置。

### Q: 开发模式下前后端无法通信？
A: 确保：
1. 后端正常启动在8001端口
2. 前端API配置正确（`frontend/src/api/api.ts`）
3. 使用相对路径调用API，项目已配置自动代理

### Q: 打包后的应用无法启动后端？
A: 确保 `fastapi-backend.exe` 已正确复制到 `frontend/resources/` 目录，并重新打包应用。

### Q: 如何修改应用图标？
A: 将图标文件放在 `frontend/public/` 目录，并在 `package.json` 的 `build` 配置中指定图标路径。

### Q: 如何支持其他平台？
A: 需要在对应平台上重新打包，并修改 `main.ts` 中的平台判断逻辑。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系

如有问题，请提交 Issue 或联系项目维护者。