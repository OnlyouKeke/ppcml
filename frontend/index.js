// Electron入口文件
const { app } = require('electron');
const path = require('path');
const fs = require('fs');

// 检查是否是开发环境
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

// 设置环境变量
process.env.NODE_ENV = isDev ? 'development' : 'production';

// 检查dist/electron目录是否存在
const electronDistPath = path.join(__dirname, 'dist', 'electron');
if (!fs.existsSync(electronDistPath)) {
  console.error('错误: dist/electron 目录不存在，请先运行 "npm run build" 或确保 Vite 已经构建了 Electron 文件');
  process.exit(1);
}

// 检查main.js文件是否存在
const mainJsPath = path.join(electronDistPath, 'main.js');
if (!fs.existsSync(mainJsPath)) {
  console.error('错误: main.js 文件不存在，请先运行 "npm run build" 或确保 Vite 已经构建了 Electron 文件');
  process.exit(1);
}

// 加载主进程文件
require('./dist/electron/main.js');