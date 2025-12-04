
from typing import List, Any, Optional, Dict

from ..bean.BaseModel import ToolParameter
from .BaseTool import BaseTool

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