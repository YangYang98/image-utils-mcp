from pydantic import BaseModel, Field
from typing import List, Any, Optional, Dict

from ..bean.BaseModel import ToolParameter
from .BaseTool import BaseTool


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
