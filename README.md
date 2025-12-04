# MCP Service

基于Model Context Protocol的服务器实现，提供工具调用和上下文管理功能。

## 功能特性

- ✅ 完整的MCP协议实现
- ✅ 多种内置工具（计算器、搜索、天气、时间等）
- ✅ FastAPI RESTful API
- ✅ Docker容器化部署
- ✅ Docker Compose编排
- ✅ 健康检查
- ✅ 可扩展工具系统

## 快速开始

### 本地开发

1. 克隆项目
```bash
git clone <repository-url>
cd image-utils-mcp
```
2. 安装依赖
```bash
pip install -r requirements.txt
```
3. 启动服务
```bash
python src/server.py
```

### Docker部署
1. 构建并启动
```bash
docker-compose up -d
```
2. 查看服务状态
```bash
docker-compose ps
```
3. 查看日志
```bash
docker-compose logs -f image-utils-mcp
```
