#!/usr/bin/env python3
"""
MCP协议使用示例

这个示例演示了如何使用MCP协议与服务进行交互，
包括工具发现、工具调用等功能。
"""

import asyncio
import json
import httpx


class MCPProtocolSimulator:
    """
    MCP协议模拟器
    
    演示MCP协议的核心功能：
    1. 工具发现 (tools/list)
    2. 工具调用 (tools/call)
    3. 初始化 (initialize)
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.request_id = 1

    def _get_next_id(self):
        """获取下一个请求ID"""
        current_id = self.request_id
        self.request_id += 1
        return current_id

    async def initialize(self):
        """
        初始化MCP连接
        
        对应MCP协议中的initialize方法
        """
        print("=== MCP协议初始化 ===")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-protocol-simulator",
                    "version": "1.0.0"
                }
            }
        }
        
        print(f"发送初始化请求:\n{json.dumps(request, indent=2, ensure_ascii=False)}\n")
        
        response = await self.client.post(self.base_url, json=request)
        result = response.json()
        
        print(f"收到初始化响应:\n{json.dumps(result, indent=2, ensure_ascii=False)}\n")
        
        return result

    async def list_tools(self):
        """
        列出所有可用工具
        
        对应MCP协议中的tools/list方法
        """
        print("=== 列出可用工具 ===")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list"
        }
        
        print(f"发送工具列表请求:\n{json.dumps(request, indent=2, ensure_ascii=False)}\n")
        
        response = await self.client.post(self.base_url, json=request)
        result = response.json()
        
        print(f"收到工具列表响应:\n{json.dumps(result, indent=2, ensure_ascii=False)}\n")
        
        # 格式化显示工具信息
        if "result" in result and "tools" in result["result"]:
            print("可用工具详情:")
            for tool in result["result"]["tools"]:
                func = tool.get("function", {})
                print(f"  - 名称: {func.get('name', 'N/A')}")
                print(f"    描述: {func.get('description', 'N/A')}")
                params = func.get("parameters", {}).get("properties", {})
                if params:
                    print("    参数:")
                    for param_name, param_info in params.items():
                        print(f"      - {param_name}: {param_info.get('type', 'any')}")
                        if "description" in param_info:
                            print(f"        描述: {param_info['description']}")
                print()
        
        return result

    async def call_tool(self, tool_name: str, arguments: dict = None):
        """
        调用指定工具
        
        对应MCP协议中的tools/call方法
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        """
        print(f"=== 调用工具: {tool_name} ===")
        
        if arguments is None:
            arguments = {}
            
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        print(f"发送工具调用请求:\n{json.dumps(request, indent=2, ensure_ascii=False)}\n")
        
        response = await self.client.post(self.base_url, json=request)
        result = response.json()
        
        print(f"收到工具调用响应:\n{json.dumps(result, indent=2, ensure_ascii=False)}\n")
        
        return result

    async def send_initialized_notification(self):
        """
        发送初始化完成通知
        
        对应MCP协议中的notifications/initialized方法
        """
        print("=== 发送初始化完成通知 ===")
        
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        print(f"发送通知:\n{json.dumps(notification, indent=2, ensure_ascii=False)}\n")
        
        response = await self.client.post(self.base_url, json=notification)
        print(f"通知发送完成，状态码: {response.status_code}\n")

    async def run_demo(self):
        """
        运行完整演示流程
        """
        try:
            # 1. 初始化连接
            await self.initialize()
            
            # 2. 发送初始化完成通知
            await self.send_initialized_notification()
            
            # 3. 列出所有工具
            await self.list_tools()
            
            # 4. 演示工具调用
            print("=" * 60)
            print("开始演示工具调用")
            print("=" * 60)
            
            # # 调用计算器工具
            # await self.call_tool(
            #     "calculator",
            #     {
            #         "operation": "multiply",
            #         "a": 15,
            #         "b": 4
            #     }
            # )
            #
            # # 调用时间工具
            # await self.call_tool(
            #     "time",
            #     {
            #         "format": "iso"
            #     }
            # )
            
            # 调用文本转图片工具
            await self.call_tool(
                "text2image",
                {
                    "title": "MCP协议示例",
                    "content": "这是使用MCP协议调用工具生成的图片内容。\n模型上下文协议(Model Context Protocol)允许AI系统与外部工具进行交互。",
                    "image_type": "BlackBgWhiteText"
                }
            )
            
            print("=" * 60)
            print("演示完成")
            print("=" * 60)
            
        except Exception as e:
            print(f"演示过程中发生错误: {e}")
        finally:
            await self.client.aclose()


async def main():
    """
    主函数
    """
    print("MCP协议使用示例")
    print("=" * 60)
    print("本示例演示了如何使用MCP协议与服务进行交互")
    print("=" * 60)
    print()
    
    # 创建MCP协议模拟器实例
    simulator = MCPProtocolSimulator()
    
    # 运行演示
    await simulator.run_demo()


if __name__ == "__main__":
    asyncio.run(main())