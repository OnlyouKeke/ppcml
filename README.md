1. 构建FastAPI后端为exe文件
首先，您需要使用PyInstaller将后端Python代码打包成exe文件：

cd backend
使用PyInstaller打包FastAPI后端

pyinstaller fastapi-backend.spec


切换到frontend目录打包

npm run electron:build