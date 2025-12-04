import asyncio
import httpx
import json


class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def list_tools(self):
        """列出所有可用工具"""
        response = await self.client.get(f"{self.base_url}/tools")
        return response.json()

    async def call_tool(self, tool_name: str, **kwargs):
        """调用工具"""
        print(f"Sending request to {tool_name} with params: {kwargs}")  # 调试信息
        response = await self.client.post(
            f"{self.base_url}/tools/{tool_name}",
            json={"arguments": kwargs}
        )
        return response.json()

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def main():
    client = MCPClient()

    try:
        # 获取工具列表
        tools = await client.list_tools()
        # print(f"{tools}")
        print("可用工具:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")

        print("\n" + "=" * 50 + "\n")

        # 调用计算器
        print("调用计算器:")
        result = await client.call_tool(
            "calculator",
            operation="add",
            a=10,
            b=5
        )
        print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

        print("\n" + "=" * 50 + "\n")

        # 获取时间
        print("获取当前时间:")
        time_result = await client.call_tool("time", format="human")
        print(f"时间: {json.dumps(time_result, indent=2, ensure_ascii=False)}")

        print("\n" + "=" * 50 + "\n")

        # 搜索示例
        print("执行搜索:")
        search_result = await client.call_tool(
            "websearch",
            query="Python MCP protocol",
            max_results=3
        )
        print(f"搜索结果: {json.dumps(search_result, indent=2, ensure_ascii=False)}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())