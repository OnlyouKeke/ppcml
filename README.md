# Electron + FastAPI + Vue3 应用

这是一个使用Electron、FastAPI和Vue3构建的桌面应用示例。

## 项目结构

```
├── backend/          # FastAPI后端
│   └── app/          # 后端应用代码
│       └── main.py   # 主应用入口
├── frontend/         # Electron + Vue3前端
│   ├── electron/     # Electron主进程代码
│   └── src/          # Vue3应用代码
└── start.ps1         # 启动脚本
```

## 技术栈

- **前端**：Vue3 + TypeScript + Pinia + Arco Design
- **后端**：FastAPI + Python
- **桌面应用**：Electron

## 开发环境要求

- Node.js 16+
- Python 3.12+
- npm 或 yarn

## 安装依赖

### 后端依赖

```bash
cd backend
pip install -e .
```

### 前端依赖

```bash
cd frontend
npm install
```

## 启动应用

使用PowerShell启动脚本：

```bash
./start.ps1
```

这将同时启动FastAPI后端和Electron前端。

## 开发指南

### 后端开发

后端使用FastAPI框架，主要代码在`backend/app/main.py`文件中。

### 前端开发

前端使用Vue3 + TypeScript，主要代码在`frontend/src`目录中。

### Electron开发

Electron相关代码在`frontend/electron`目录中。

## 构建应用

```bash
cd frontend
npm run electron:build
```

构建后的应用将在`frontend/dist`目录中。

## 许可证

MIT