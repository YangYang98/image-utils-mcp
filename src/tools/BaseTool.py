# ==================== 工具基类 ====================
from typing import List, Any, Optional, Dict

from ..bean.BaseModel import ToolDefinition, ToolParameter


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