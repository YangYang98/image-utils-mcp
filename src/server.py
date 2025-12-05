import asyncio
import logging
import sys
import json
import os

# 设置环境变量确保使用UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 将src目录添加到Python路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from contextlib import asynccontextmanager
from typing import List, Any, Dict
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 修改导入路径为绝对导入
from src.tools.Text2ImageTool import Text2ImageTool
from src.bean.BaseModel import ToolDefinition, ToolCallResponse, ToolCallRequest, ErrorResponse, ToolParameter
from src.tools.CalculatorTool import CalculatorTool
from src.tools.ImageProcessingTool import ImageProcessingTool
from src.tools.TimeTool import TimeTool
from src.tools.WeatherTool import WeatherTool
from src.tools.WebSearchTool import WebSearchTool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 强制设置编码为UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())


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
        logger.info(f"准备调用工具: {tool_name}, 参数: {arguments}")
        
        if tool_name not in self.tools:
            logger.error(f"工具不存在: {tool_name}")
            raise ValueError(f"工具不存在: {tool_name}")

        tool = self.tools[tool_name]

        try:
            # 验证参数
            tool_def = tool.get_definition()
            logger.debug(f"工具 {tool_name} 的定义: {tool_def}")
            
            missing_params = [p for p in tool_def.required if p not in arguments]
            if missing_params:
                error_msg = f"缺少必需参数: {', '.join(missing_params)}, 当前参数: {arguments}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 执行工具
            logger.info(f"开始执行工具: {tool_name}")
            result = await tool.execute(**arguments)
            logger.info(f"工具 {tool_name} 执行完成")

            # 格式化响应
            if isinstance(result, dict):
                content = [result]
            else:
                content = [{"type": "text", "text": str(result)}]
            
            logger.debug(f"工具 {tool_name} 返回结果: {content}")
            return content

        except Exception as e:
            logger.error(f"调用工具 {tool_name} 失败: {e}", exc_info=True)
            raise ValueError(f"工具执行失败: {str(e)}")


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
        print(f"Sending request to {tool_name} with params: {request.arguments}")
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


# ==================== MCP 协议支持 ====================

# 存储活跃的 JSON-RPC 连接
active_connections = {}


@app.post("/")
async def mcp_json_rpc_handler(request: Request):
    """处理 JSON-RPC 请求 (MCP 协议)"""
    try:
        # 获取原始请求体
        body_bytes = await request.body()
        
        # 尝试多种编码方式解码
        body_str = None
        errors = []
        
        # 首先尝试UTF-8编码
        try:
            body_str = body_bytes.decode('utf-8')
            logger.info(f"成功使用UTF-8解码请求体，长度: {len(body_bytes)} 字节")
        except UnicodeDecodeError as e:
            errors.append(f"UTF-8 decode failed: {str(e)}")
            
        # 如果UTF-8失败，尝试系统默认编码
        if body_str is None:
            try:
                import locale
                default_encoding = locale.getpreferredencoding()
                body_str = body_bytes.decode(default_encoding)
                logger.warning(f"Using system default encoding: {default_encoding}")
            except UnicodeDecodeError as e:
                errors.append(f"Default encoding ({default_encoding}) decode failed: {str(e)}")
                
        # 如果系统默认编码也失败，尝试CP936(简体中文)
        if body_str is None:
            try:
                body_str = body_bytes.decode('cp936')
                logger.warning("Using CP936 encoding")
            except UnicodeDecodeError as e:
                errors.append(f"CP936 decode failed: {str(e)}")
                
        # 如果所有编码都失败，记录错误并返回
        if body_str is None:
            logger.error(f"All decode attempts failed: {errors}")
            raise ValueError(f"无法解码请求体: {errors}")

        # 确保JSON解析时保持Unicode字符
        body = json.loads(body_str)
        logger.info(f"收到 JSON-RPC 请求: {body}")
        
        # 处理 initialize 请求
        if body.get("method") == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        }
                    },
                    "serverInfo": {
                        "name": "image-utils-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            return response
            
        # 处理 tools/list 请求
        elif body.get("method") == "tools/list":
            tools = await app.state.mcp_server.list_tools()
            # 转换为 MCP 协议格式
            mcp_tools = []
            for tool in tools:
                # 将参数转换为正确的格式
                properties = {}
                for name, param in tool.parameters.items():
                    properties[name] = {
                        "type": str(param.type)
                    }
                    if param.description:
                        properties[name]["description"] = str(param.description)
                    if param.enum:
                        properties[name]["enum"] = [str(e) for e in param.enum]
                    if param.default is not None:
                        properties[name]["default"] = str(param.default)
                
                mcp_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": tool.required
                        }
                    }
                })
                
            response = {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "tools": mcp_tools
                }
            }
            return response
            
        # 处理 tools/call 请求
        elif body.get("method") == "tools/call":
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            # 对参数中的字符串值进行额外的编码检查和修复
            fixed_arguments = {}
            for key, value in arguments.items():
                if isinstance(value, str):
                    # 检查字符串是否包含问号，这可能意味着编码问题
                    if '?' in value and body_str.count('?') >= len(value) // 3:
                        logger.warning(f"检测到参数 '{key}' 可能存在编码问题: {value}")
                        # 尝试重新解码
                        try:
                            # 使用原始字节重新解码
                            raw_bytes = value.encode('latin1')  # 获取原始字节
                            fixed_value = raw_bytes.decode('utf-8')
                            fixed_arguments[key] = fixed_value
                            logger.info(f"修复了参数 '{key}' 的编码: {fixed_value}")
                        except Exception as e:
                            logger.error(f"修复参数 '{key}' 编码失败: {e}")
                            fixed_arguments[key] = value
                    else:
                        fixed_arguments[key] = value
                else:
                    fixed_arguments[key] = value

            logger.info(f"准备调用工具: {tool_name}, 参数: {fixed_arguments}")

            try:
                content = await app.state.mcp_server.call_tool(tool_name, fixed_arguments)
                response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "content": content
                    }
                }
                return response
            except Exception as e:
                logger.error(f"执行工具 '{tool_name}' 时出错: {e}", exc_info=True)
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }

        # 处理 notifications/initialized 请求
        elif body.get("method") == "notifications/initialized":
            # 这是一个通知，不需要响应
            return Response(status_code=204)

        # 未知方法
        else:
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {body.get('method')}"
                }
            }

    except UnicodeDecodeError as e:
        logger.error(f"字符编码错误: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Character encoding error: {str(e)}"
            }
        }
    except Exception as e:
        logger.error(f"处理 JSON-RPC 请求时出错: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


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

def run_stdio():
    """以STDIO模式运行MCP服务器"""
    print("STDIO模式尚未实现，将在未来版本中添加")
    sys.exit(1)


if __name__ == "__main__":
    import uvicorn

    # 检查是否以STDIO模式运行
    if "--stdio" in sys.argv:
        run_stdio()
    else:
        # 获取配置
        host = "0.0.0.0"
        port = 8000
        log_level = "info"

        # 启动服务器
        uvicorn.run(
            "src.server:app",
            host=host,
            port=port,
            reload=True,  # 开发时启用热重载
            log_level=log_level
        )