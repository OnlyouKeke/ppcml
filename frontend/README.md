# Electron + FastAPI + Vue3 应用

这是一个使用 Electron、FastAPI 和 Vue3 构建的桌面应用程序示例。

## 技术栈

### 前端
- Vue 3
- TypeScript
- Pinia (状态管理)
- Vue Router
- Arco Design Vue (UI组件库)
- Vite (构建工具)

### 后端
- FastAPI (Python)

### 桌面应用
- Electron

## 项目结构

```
├── backend/             # FastAPI 后端
│   ├── main.py          # 后端入口文件
│   └── ...
├── frontend/            # Vue3 前端
│   ├── electron/        # Electron 相关文件
│   │   ├── main.ts      # Electron 主进程
│   │   └── preload.ts   # 预加载脚本
│   ├── public/          # 静态资源
│   ├── src/             # 源代码
│   │   ├── api/         # API 通信
│   │   ├── assets/      # 资源文件
│   │   ├── components/  # 组件
│   │   ├── router/      # 路由
│   │   ├── store/       # Pinia 状态管理
│   │   ├── types/       # TypeScript 类型
│   │   ├── views/       # 视图组件
│   │   ├── App.vue      # 根组件
│   │   └── main.ts      # 前端入口文件
│   ├── index.html       # HTML 模板
│   ├── package.json     # 依赖和脚本
│   ├── tsconfig.json    # TypeScript 配置
│   └── vite.config.ts   # Vite 配置
└── ...
```

## 开发指南

### 安装依赖

```bash
# 安装前端依赖
cd frontend
npm install

# 安装后端依赖
cd ../backend
pip install -r requirements.txt
```

### 开发模式

```bash
# 启动前端开发服务器
cd frontend
npm run dev

# 在另一个终端启动后端
cd backend
python main.py
```

### 构建应用

```bash
# 构建前端
cd frontend
npm run build

# 打包 Electron 应用
npm run electron:build
```

## 通信架构

本应用采用以下通信架构：

1. Vue3 前端通过 HTTP 请求与 FastAPI 后端通信
2. Electron 主进程负责启动 FastAPI 后端服务
3. Electron 预加载脚本提供安全的 IPC 通信接口

## 许可证

MIT