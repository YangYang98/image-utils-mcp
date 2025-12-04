import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .tools.Text2ImageTool import Text2ImageTool
from .bean.BaseModel import ToolDefinition, ToolCallResponse, ToolCallRequest, ErrorResponse
from .tools.CalculatorTool import CalculatorTool
from .tools.ImageProcessingTool import ImageProcessingTool
from .tools.TimeTool import TimeTool
from .tools.WeatherTool import WeatherTool
from .tools.WebSearchTool import WebSearchTool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MCP 服务器实现 ====================

class MCPServer:
    """MCP 服务器核心类"""

    def __init__(self):
        self.tools = {}
        self._initialize_tools()

    def _initialize_tools(self):
        """初始化所有工具"""
        tool_classes = [
            CalculatorTool,
            WeatherTool,
            ImageProcessingTool,
            WebSearchTool,
            TimeTool,
            Text2ImageTool
        ]

        for tool_class in tool_classes:
            try:
                tool = tool_class()
                self.tools[tool.name] = tool
                logger.info(f"已注册工具: {tool.name}")
            except Exception as e:
                logger.error(f"注册工具 {tool_class.__name__} 失败: {e}")

    async def list_tools(self) -> List[ToolDefinition]:
        """列出所有可用工具"""
        return [tool.get_definition() for tool in self.tools.values()]

    async def call_tool(self, tool_name: str, arguments: dict) -> List[Dict[str, Any]]:
        """调用特定工具"""
        if tool_name not in self.tools:
            raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")

        tool = self.tools[tool_name]

        try:
            # 验证参数
            tool_def = tool.get_definition()
            missing_params = [p for p in tool_def.required if p not in arguments]
            if missing_params:
                raise HTTPException(
                    status_code=400,
                    detail=f"缺少必需参数: {', '.join(missing_params)}, 当前参数: {arguments}"
                )

            # 执行工具
            result = await tool.execute(**arguments)

            # 格式化响应
            if isinstance(result, dict):
                content = [result]
            else:
                content = [{"type": "text", "text": str(result)}]

            return content

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"调用工具 {tool_name} 失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"工具执行失败: {str(e)}"
            )


# ==================== FastAPI 应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化 MCP 服务器
    app.state.mcp_server = MCPServer()
    logger.info(f"MCP 服务器已初始化，共加载 {len(app.state.mcp_server.tools)} 个工具")

    yield

    # 关闭时清理
    logger.info("MCP 服务器关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="MCP 服务",
    description="基于 FastAPI 的 Model Context Protocol 服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API 端点 ====================

@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "MCP 服务",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "tool_call": "/tools/{tool_name}",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "mcp-service",
        "tools_loaded": len(app.state.mcp_server.tools),
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/tools", response_model=List[ToolDefinition])
async def list_tools():
    """列出所有可用工具"""
    try:
        tools = await app.state.mcp_server.list_tools()
        return tools
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/{tool_name}", response_model=ToolCallResponse)
async def call_tool(tool_name: str, request: ToolCallRequest):
    """调用工具"""
    try:
        # print(f"Sending request to {tool_name} with params: {request.arguments}")
        content = await app.state.mcp_server.call_tool(tool_name, request.arguments)
        return ToolCallResponse(content=content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"调用工具 {tool_name} 时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools/{tool_name}/definition")
async def get_tool_definition(tool_name: str):
    """获取特定工具的定义"""
    if tool_name not in app.state.mcp_server.tools:
        raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")

    tool = app.state.mcp_server.tools[tool_name]
    return tool.get_definition()


# ==================== 错误处理 ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            details={"tool": request.url.path}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="内部服务器错误",
            details={"message": str(exc)}
        ).dict()
    )


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    import uvicorn

    # 获取配置
    host = "0.0.0.0"
    port = 8000
    log_level = "info"

    # 启动服务器
    uvicorn.run(
        "src.server:app",  # 如果这个文件是 server.py，并且从根目录运行，可以这样写
        host=host,
        port=port,
        reload=True,  # 开发时启用热重载
        log_level=log_level
    )
