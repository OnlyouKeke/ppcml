1. 构建FastAPI后端为exe文件
首先，您需要使用PyInstaller将后端Python代码打包成exe文件：

cd backend
使用PyInstaller打包FastAPI后端


pyinstaller fastapi-backend.spec
查看当前目录内容

已查看目录
backend
15 个结果
使用PyInstaller打包FastAPI后端

终端已运行
pyinstaller fastapi-backend.spec
确认当前目录并列出文件

终端已运行
pwd
切换到backend目录并打包

npm run electron:build