
from typing import List, Any, Optional, Dict

from ..bean.BaseModel import ToolParameter
from .BaseTool import BaseTool


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