"""
MCP Server 最简示例 - Math Server

运行：python mcpTest.py
"""

from mcp.server.fastmcp import FastMCP

# ============================================================================
# 第1步：创建 FastMCP 实例
# ============================================================================
mcp = FastMCP("math-server", port=8000)


# ============================================================================
# 第2步：注册 Resource（资源） - 提供数据访问
# ============================================================================
@mcp.resource("math://constants/{name}")
async def get_constant(name: str) -> str:
    """获取数学常量
    
    参数:
        name: 常量名称（pi, e, golden_ratio）
    """
    constants = {
        "pi": "3.14159265358979",
        "e": "2.71828182845904",
        "golden_ratio": "1.61803398874989"
    }
    if name in constants:
        return f"{name} = {constants[name]}"
    return f"未知常量: {name}"


# ============================================================================
# 第3步：注册 Tool（工具） - 执行计算操作
# ============================================================================
@mcp.tool()
async def add(a: float, b: float) -> str:
    """两数相加
    
    参数:
        a: 第一个数
        b: 第二个数
    """
    result = a + b
    return f"{a} + {b} = {result}"


@mcp.tool()
async def multiply(a: float, b: float) -> str:
    """两数相乘
    
    参数:
        a: 第一个数
        b: 第二个数
    """
    result = a * b
    return f"{a} × {b} = {result}"


@mcp.tool()
async def power(base: float, exponent: float) -> str:
    """计算幂
    
    参数:
        base: 底数
        exponent: 指数
    """
    result = base ** exponent
    return f"{base}^{exponent} = {result}"


# ============================================================================
# 第4步：注册 Prompt（提示模板） - 预设指令
# ============================================================================
@mcp.prompt()
async def calculate_expression(expression: str) -> str:
    """生成计算表达式的提示
    
    参数:
        expression: 要计算的数学表达式
    """
    return f"""请计算以下数学表达式: {expression}

使用可用的工具（add, multiply, power）来完成计算。
请逐步展示计算过程。
"""


# ============================================================================
# 第5步：启动服务
# ============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("Math MCP Server 启动中...")
    print("=" * 50)
    print("端口: 8000")
    print("传输模式: SSE")
    print("访问地址: http://localhost:8000/sse")
    print("=" * 50)
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    # 最简单的启动方式
    mcp.run(transport="sse")
