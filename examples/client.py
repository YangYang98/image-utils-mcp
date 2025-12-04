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
        # print("调用计算器:")
        # result = await client.call_tool(
        #     "calculator",
        #     operation="add",
        #     a=10,
        #     b=5
        # )
        # print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        #
        # print("\n" + "=" * 50 + "\n")
        #
        # # 获取时间
        # print("获取当前时间:")
        # time_result = await client.call_tool("time", format="human")
        # print(f"时间: {json.dumps(time_result, indent=2, ensure_ascii=False)}")
        #
        # print("\n" + "=" * 50 + "\n")
        #
        # # 搜索示例
        # print("执行搜索:")
        # search_result = await client.call_tool(
        #     "websearch",
        #     query="Python MCP protocol",
        #     max_results=3
        # )
        # print(f"搜索结果: {json.dumps(search_result, indent=2, ensure_ascii=False)}")

        print("执行图片处理:")
        image_result = await client.call_tool(
            "text2image",
            title="智能分页生成",
            content="""小兔子最近总是失眠，晚上翻来覆去睡不着。

她抱着枕头，躺在床上，无奈地看着天花板。

小狐狸发现了小兔子在烦恼，转过身来心疼地问：

"怎么了，小兔子？是不是有心事？"

小兔子摇了摇头，皱着眉说："不知道，就是怎么都睡不着，

脑子里乱七八糟的。"

小狐狸想了想，温柔地笑着说："那我给你讲个睡前故事吧，

听了你就能快点入睡了。"

小兔子的眼睛亮了一下，但又有些挑剔地问："那你讲什么

故事呢？我喜欢有剧情曲折的，但又不能太吓人，要有趣但

又不能太复杂，要不然又该睡不着了。""",
            image_type="BlackBgWhiteText"
        )
        print(f"执行图片处理: {json.dumps(image_result, indent=2, ensure_ascii=False)}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())