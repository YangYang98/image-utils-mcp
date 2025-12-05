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

## 与MCP客户端集成

本服务支持与多种MCP客户端集成，包括:
- Cursor IDE
- VS Code with MCP extension
- Claude Desktop
- MCP Inspector

### 配置方式

#### HTTP模式
在支持HTTP连接的MCP客户端中，配置以下URL:
```
http://localhost:8000
```

#### STDIO模式
对于支持STDIO启动模式的客户端，使用以下命令启动服务:
```bash
python src/server.py --stdio
```

### 客户端配置示例

#### Cursor配置
在Cursor中，在设置中添加一个新的MCP服务器，类型选择HTTP，URL填写:
```
http://localhost:8000
```

#### VS Code配置
在VS Code中安装MCP扩展后，在设置中添加MCP服务器:
```json
{
  "mcp.servers": {
    "image-utils": {
      "type": "http",
      "url": "http://localhost:8000"
    }
  }
}
```

#### Claude Desktop配置
在Claude Desktop配置文件中添加:
```json
{
  "mcpServers": {
    "image-utils": {
      "command": "python",
      "args": ["src/server.py", "--stdio"]
    }
  }
}
```

## 工具列表和参数说明

### 调用规范
调用MCP工具时，必须向`/tools/{tool_name}`端点发送POST请求，其中{tool_name}为具体工具名称；`/tools`根端点仅支持GET请求用于获取工具列表，不支持POST方法。

每个MCP工具必须提供清晰的参数说明，包括参数名称、类型、是否必需、默认值及用途描述，确保大模型能正确理解和调用。

### 可用工具

#### Calculator（计算器）
执行基本数学运算
- **参数**:
  - `operation`: 运算类型（枚举值: add, subtract, multiply, divide）
  - `a`: 第一个数字
  - `b`: 第二个数字

#### Weather（天气查询）
获取指定地点的天气信息
- **参数**:
  - `location`: 地点名称

#### Image Processing（图像处理）
执行各种图像处理操作
- **参数**:
  - `image_path`: 图像路径
  - `operation`: 处理操作（枚举值: resize, blur, rotate）

#### Web Search（网络搜索）
在网络上搜索信息
- **参数**:
  - `query`: 搜索关键词
  - `max_results`: 最大结果数量（可选，默认为5）

#### Time（时间获取）
获取当前时间
- **参数**:
  - `format`: 时间格式（枚举值: iso, human, timestamp，默认为iso）

#### Text2Image（文字转图片）
将文本转换为图片
- **参数**:
  - `title`: 标题
  - `content`: 正文内容
  - `image_type`: 图片类型（枚举值: BlackBgWhiteText，默认为BlackBgWhiteText）

### 字符编码注意事项

为确保中文等非ASCII字符正确传输和处理，请注意以下事项：

1. 客户端发送请求时请确保使用UTF-8编码
2. HTTP请求头中应包含`Content-Type: application/json; charset=utf-8`
3. 服务器端会自动处理多种编码格式，但如果发现中文显示为问号，请检查客户端编码设置

## 项目运行命令

Python项目正确运行方式：cd到项目根目录后执行`python -m src.server`，或进入src目录后执行`python server.py`