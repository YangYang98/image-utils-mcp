import asyncio
import json
import logging
import sys
from typing import List, Any, Optional, Dict
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

class ToolParameter(BaseModel):
    """工具参数定义"""
    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = None
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, ToolParameter]
    required: List[str] = []


class ToolCallRequest(BaseModel):
    """工具调用请求"""
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    """工具调用响应"""
    content: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    details: Optional[Dict[str, Any]] = None


# ==================== 工具基类 ====================

class BaseTool:
    """工具基类"""

    def __init__(self):
        self.name = self.__class__.__name__.replace('Tool', '').lower()
        self.description = getattr(self, 'description', 'No description provided')

    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        raise NotImplementedError

    def get_definition(self) -> ToolDefinition:
        """获取工具定义"""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self._get_parameters(),
            required=self._get_required_parameters()
        )

    def _get_parameters(self) -> Dict[str, ToolParameter]:
        """获取参数定义（子类覆盖）"""
        return {}

    def _get_required_parameters(self) -> List[str]:
        """获取必需参数列表（子类覆盖）"""
        return []


# ==================== 具体工具实现 ====================

class CalculatorTool(BaseTool):
    """计算器工具"""

    def __init__(self):
        super().__init__()
        self.description = "执行数学计算：加法、减法、乘法、除法"

    def _get_parameters(self) -> Dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                type="string",
                description="数学运算类型",
                enum=["add", "subtract", "multiply", "divide"]
            ),
            "a": ToolParameter(
                type="number",
                description="第一个数字"
            ),
            "b": ToolParameter(
                type="number",
                description="第二个数字"
            )
        }

    def _get_required_parameters(self) -> List[str]:
        return ["operation", "a", "b"]

    async def execute(self, operation: str, a: float, b: float) -> Dict[str, Any]:
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    raise ValueError("Division by zero")
                result = a / b
            else:
                raise ValueError(f"未知操作: {operation}")

            return {
                "type": "text",
                "text": f"计算结果: {a} {operation} {b} = {result}",
                "result": result
            }
        except Exception as e:
            return {
                "type": "error",
                "text": f"计算错误: {str(e)}"
            }


class WeatherTool(BaseTool):
    """天气查询工具"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.description = "查询城市天气信息"
        self.api_key = api_key or "your-api-key"

    def _get_parameters(self) -> Dict[str, ToolParameter]:
        return {
            "city": ToolParameter(
                type="string",
                description="城市名称"
            ),
            "country": ToolParameter(
                type="string",
                description="国家代码（可选）",
                default="CN"
            )
        }

    def _get_required_parameters(self) -> List[str]:
        return ["city"]

    async def execute(self, city: str, country: str = "CN") -> Dict[str, Any]:
        try:
            # 这里可以使用真实的天气API，例如：
            # https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}
            # 为了示例，我们模拟返回数据

            # 模拟不同的天气数据
            weather_conditions = ["晴天", "多云", "小雨", "阴天", "阵雨"]
            import random
            temperature = random.uniform(15.0, 30.0)

            return {
                "type": "text",
                "text": f"{city} ({country}) 的天气：",
                "content": {
                    "city": city,
                    "country": country,
                    "temperature": round(temperature, 1),
                    "condition": random.choice(weather_conditions),
                    "humidity": random.randint(40, 90),
                    "wind_speed": random.uniform(1.0, 10.0)
                }
            }
        except Exception as e:
            return {
                "type": "error",
                "text": f"天气查询失败: {str(e)}"
            }


class ImageProcessingTool(BaseTool):
    """图像处理工具"""

    def __init__(self):
        super().__init__()
        self.description = "图像处理工具：调整大小、转换格式、应用滤镜等"

    def _get_parameters(self) -> Dict[str, ToolParameter]:
        return {
            "action": ToolParameter(
                type="string",
                description="处理动作",
                enum=["resize", "convert", "rotate", "filter"]
            ),
            "image_url": ToolParameter(
                type="string",
                description="图像URL或base64编码"
            ),
            "width": ToolParameter(
                type="integer",
                description="调整宽度（像素）",
                default=800
            ),
            "height": ToolParameter(
                type="integer",
                description="调整高度（像素）",
                default=600
            ),
            "format": ToolParameter(
                type="string",
                description="输出格式",
                enum=["jpg", "png", "webp", "bmp"],
                default="jpg"
            )
        }

    def _get_required_parameters(self) -> List[str]:
        return ["action", "image_url"]

    async def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            action = kwargs.get("action")
            image_url = kwargs.get("image_url")

            # 这里可以实现实际的图像处理逻辑
            # 为了示例，我们模拟处理结果

            return {
                "type": "text",
                "text": f"图像处理完成: {action}",
                "content": {
                    "action": action,
                    "original_url": image_url,
                    "processed_url": f"https://example.com/processed/{hash(image_url)}.jpg",
                    "status": "success",
                    "message": f"成功执行 {action} 操作"
                }
            }
        except Exception as e:
            return {
                "type": "error",
                "text": f"图像处理失败: {str(e)}"
            }


class WebSearchTool(BaseTool):
    """网络搜索工具"""

    def __init__(self):
        super().__init__()
        self.description = "搜索网络信息"

    def _get_parameters(self) -> Dict[str, ToolParameter]:
        return {
            "query": ToolParameter(
                type="string",
                description="搜索关键词"
            ),
            "max_results": ToolParameter(
                type="integer",
                description="最大结果数",
                default=5
            )
        }

    def _get_required_parameters(self) -> List[str]:
        return ["query"]

    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        try:
            # 模拟搜索延迟
            await asyncio.sleep(0.5)

            import random
            results = []
            for i in range(max_results):
                results.append({
                    "title": f"关于 '{query}' 的搜索结果 {i + 1}",
                    "snippet": f"这是关于 {query} 的搜索结果摘要。相关内容示例...",
                    "url": f"https://example.com/search?q={query}&result={i + 1}",
                    "relevance": round(random.uniform(0.7, 1.0), 2)
                })

            return {
                "type": "text",
                "text": f"找到 {len(results)} 条关于 '{query}' 的结果:",
                "content": {
                    "query": query,
                    "results": results,
                    "total": len(results)
                }
            }
        except Exception as e:
            return {
                "type": "error",
                "text": f"搜索失败: {str(e)}"
            }


class TimeTool(BaseTool):
    """时间工具"""

    def __init__(self):
        super().__init__()
        self.description = "获取当前时间信息"

    def _get_parameters(self) -> Dict[str, ToolParameter]:
        return {
            "format": ToolParameter(
                type="string",
                description="时间格式",
                enum=["iso", "timestamp", "human", "full"],
                default="human"
            )
        }

    async def execute(self, format: str = "human") -> Dict[str, Any]:
        try:
            from datetime import datetime

            now = datetime.now()

            if format == "iso":
                result = now.isoformat()
            elif format == "timestamp":
                result = now.timestamp()
            elif format == "human":
                result = now.strftime("%Y年%m月%d日 %H:%M:%S")
            elif format == "full":
                result = {
                    "iso": now.isoformat(),
                    "timestamp": now.timestamp(),
                    "year": now.year,
                    "month": now.month,
                    "day": now.day,
                    "hour": now.hour,
                    "minute": now.minute,
                    "second": now.second,
                    "weekday": now.strftime("%A")
                }
            else:
                result = now.isoformat()

            return {
                "type": "text",
                "text": f"当前时间: {result}" if isinstance(result, str) else "当前时间信息:",
                "content": result if isinstance(result, dict) else {"time": result}
            }
        except Exception as e:
            return {
                "type": "error",
                "text": f"获取时间失败: {str(e)}"
            }


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
            TimeTool
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
        "server:app",  # 如果这个文件是 server.py，并且从根目录运行，可以这样写
        host=host,
        port=port,
        reload=True,  # 开发时启用热重载
        log_level=log_level
    )