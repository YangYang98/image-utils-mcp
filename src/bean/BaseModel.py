from pydantic import BaseModel, Field
from typing import List, Any, Optional, Dict

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
