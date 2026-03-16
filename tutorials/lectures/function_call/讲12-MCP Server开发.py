"""
讲12 | MCP Server开发 - 官方标准实现（SSE模式）

安装依赖：pip install mcp httpx uvicorn starlette
运行：python "讲12-MCP Server开发.py"
"""

import os
import json
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from multiprocessing import Process

try:
    from mcp.server.fastmcp import FastMCP
    import httpx
except ImportError:
    print("请先安装依赖: pip install mcp httpx uvicorn starlette")
    raise


# ============================================================================
# 练习1：文件Server
# ============================================================================

def create_file_server():
    """文件系统MCP Server"""
    mcp = FastMCP("file-server",port=8000)
    # 使用相对于当前文件的file目录
    BASE_PATH = Path(__file__).parent / "file"
    BASE_PATH.mkdir(exist_ok=True)  # 确保目录存在
    
    @mcp.resource("file://documents/{path}")
    async def read_file(path: str) -> str:
        """从documents目录读取文件
        
        参数:
            path: 文件的相对路径
        """
        full_path = BASE_PATH / path
        if not full_path.exists():
            return f"错误: 文件不存在: {path}"
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"读取文件错误: {str(e)}"
    
    @mcp.tool()
    async def list_files(directory: str = "") -> str:
        """列出目录中的文件
        
        参数:
            directory: 子目录路径（可选，默认为根目录）
        """
        target_path = BASE_PATH / directory if directory else BASE_PATH
        
        if not target_path.exists():
            return json.dumps({"error": "目录不存在"})
        
        files = []
        for item in target_path.iterdir():
            if item.is_file():
                files.append({
                    "name": item.name,
                    "size": item.stat().st_size,
                    "modified": item.stat().st_mtime
                })
        
        return json.dumps({
            "directory": directory or "/",
            "count": len(files),
            "files": files
        }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def search_files(query: str) -> str:
        """按文件名搜索文件
        
        参数:
            query: 搜索关键词
        """
        results = []
        for root, dirs, files in os.walk(BASE_PATH):
            for file in files:
                if query.lower() in file.lower():
                    full_path = Path(root) / file
                    results.append(str(full_path.relative_to(BASE_PATH)))
                    if len(results) >= 20:
                        break
        
        return json.dumps({
            "query": query,
            "count": len(results),
            "results": results
        }, ensure_ascii=False, indent=2)
    
    return mcp


# ============================================================================
# 练习2：笔记Server
# ============================================================================

def create_note_server():
    """笔记管理MCP Server"""
    mcp = FastMCP("note-server",port=8001)
    NOTES_DIR = Path.home() / ".mcp_notes"
    NOTES_DIR.mkdir(exist_ok=True)
    
    @mcp.resource("note://{note_id}")
    async def read_note(note_id: str) -> str:
        """根据ID读取笔记
        
        参数:
            note_id: 笔记标识符
        """
        note_file = NOTES_DIR / f"{note_id}.json"
        if not note_file.exists():
            return json.dumps({"error": f"笔记不存在: {note_id}"})
        
        with open(note_file, "r", encoding="utf-8") as f:
            return f.read()
    
    @mcp.tool()
    async def create_note(title: str, content: str, tags: list[str] = None) -> str:
        """创建新笔记
        
        参数:
            title: 笔记标题
            content: 笔记内容
            tags: 可选的标签列表
        """
        note_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        note_file = NOTES_DIR / f"{note_id}.json"
        with open(note_file, "w", encoding="utf-8") as f:
            json.dump(note, f, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "success": True,
            "note_id": note_id,
            "message": "笔记创建成功"
        }, ensure_ascii=False)
    
    @mcp.tool()
    async def list_notes() -> str:
        """列出所有笔记"""
        notes = []
        for note_file in NOTES_DIR.glob("*.json"):
            with open(note_file, "r", encoding="utf-8") as f:
                note = json.load(f)
            notes.append({
                "id": note["id"],
                "title": note["title"],
                "tags": note.get("tags", []),
                "created_at": note.get("created_at")
            })
        
        return json.dumps({
            "count": len(notes),
            "notes": sorted(notes, key=lambda x: x["created_at"], reverse=True)
        }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def search_notes(query: str) -> str:
        """按标题或内容搜索笔记
        
        参数:
            query: 搜索关键词
        """
        results = []
        query_lower = query.lower()
        
        for note_file in NOTES_DIR.glob("*.json"):
            with open(note_file, "r", encoding="utf-8") as f:
                note = json.load(f)
            
            if query_lower in note["title"].lower() or query_lower in note["content"].lower():
                results.append({
                    "id": note["id"],
                    "title": note["title"],
                    "preview": note["content"][:100] + "..." if len(note["content"]) > 100 else note["content"]
                })
        
        return json.dumps({
            "query": query,
            "count": len(results),
            "results": results
        }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def delete_note(note_id: str) -> str:
        """删除笔记
        
        参数:
            note_id: 笔记标识符
        """
        note_file = NOTES_DIR / f"{note_id}.json"
        if not note_file.exists():
            return json.dumps({"success": False, "error": "笔记不存在"})
        
        note_file.unlink()
        return json.dumps({"success": True, "message": "笔记已删除"})
    
    return mcp


# ============================================================================
# 练习3：数据库Server（模拟数据库）
# ============================================================================

def create_database_server():
    """模拟数据库MCP Server（不使用真实数据库）"""
    mcp = FastMCP("database-server",port=8002)
    
    # 模拟数据库 - 使用内存字典存储
    MOCK_DB = {
        "users": [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com", "created_at": "2024-01-01T10:00:00"},
            {"id": 2, "name": "李四", "email": "lisi@example.com", "created_at": "2024-01-02T11:00:00"},
            {"id": 3, "name": "王五", "email": "wangwu@example.com", "created_at": "2024-01-03T12:00:00"},
        ],
        "tasks": [
            {"id": 1, "user_id": 1, "title": "完成项目文档", "completed": False, "created_at": "2024-01-01T14:00:00"},
            {"id": 2, "user_id": 1, "title": "代码审查", "completed": True, "created_at": "2024-01-02T15:00:00"},
            {"id": 3, "user_id": 2, "title": "团队会议", "completed": False, "created_at": "2024-01-03T16:00:00"},
        ]
    }
    
    # 用于生成自增ID
    ID_COUNTER = {"users": 4, "tasks": 4}
    
    @mcp.resource("db://table/{table_name}")
    async def read_table(table_name: str) -> str:
        """从模拟数据库表读取数据
        
        参数:
            table_name: 表名
        """
        if table_name not in MOCK_DB:
            return json.dumps({"error": f"表不存在: {table_name}"})
        
        rows = MOCK_DB[table_name]
        return json.dumps({
            "table": table_name,
            "count": len(rows),
            "rows": rows
        }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def list_tables() -> str:
        """列出所有表"""
        tables = list(MOCK_DB.keys())
        return json.dumps({
            "count": len(tables),
            "tables": tables
        }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def query_database(sql: str) -> str:
        """在模拟数据库上执行简单的SELECT查询
        
        参数:
            sql: SQL SELECT语句（支持基本的SELECT语法）
        """
        if not sql.strip().upper().startswith("SELECT"):
            return json.dumps({"error": "只允许SELECT查询"})
        
        # 简单解析SQL - 提取表名
        sql_upper = sql.upper()
        if "FROM" not in sql_upper:
            return json.dumps({"error": "SQL语法错误：缺少FROM子句"})
        
        # 提取表名（简单解析）
        try:
            from_index = sql_upper.index("FROM")
            after_from = sql.split()[sql_upper.split().index("FROM") + 1].strip().rstrip(";")
            table_name = after_from.split()[0]
            
            if table_name not in MOCK_DB:
                return json.dumps({"error": f"表不存在: {table_name}"})
            
            rows = MOCK_DB[table_name]
            
            # 简单的WHERE过滤（支持基本条件）
            if "WHERE" in sql_upper:
                # 这里只做演示，实际不执行复杂解析
                pass
            
            return json.dumps({
                "count": len(rows),
                "rows": rows,
                "note": "模拟查询：返回表中所有数据"
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"查询解析错误: {str(e)}"})
    
    @mcp.tool()
    async def insert_record(table: str, data: dict[str, Any]) -> str:
        """向表中插入记录（模拟）
        
        参数:
            table: 表名
            data: 列-值对的字典
        """
        if table not in MOCK_DB:
            return json.dumps({"error": f"表不存在: {table}"})
        
        # 生成新ID
        new_id = ID_COUNTER[table]
        ID_COUNTER[table] += 1
        
        # 创建新记录
        new_record = {"id": new_id, **data}
        if "created_at" not in new_record:
            new_record["created_at"] = datetime.now().isoformat()
        
        # 添加到模拟数据库
        MOCK_DB[table].append(new_record)
        
        return json.dumps({
            "success": True,
            "id": new_id,
            "message": f"记录已插入到 {table} 表"
        }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def update_record(table: str, record_id: int, data: dict[str, Any]) -> str:
        """更新表中的记录（模拟）
        
        参数:
            table: 表名
            record_id: 记录ID
            data: 要更新的列-值对
        """
        if table not in MOCK_DB:
            return json.dumps({"error": f"表不存在: {table}"})
        
        # 查找记录
        for record in MOCK_DB[table]:
            if record["id"] == record_id:
                # 更新字段
                for key, value in data.items():
                    record[key] = value
                record["updated_at"] = datetime.now().isoformat()
                
                return json.dumps({
                    "success": True,
                    "message": f"记录 {record_id} 已更新"
                }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "success": False,
            "error": f"未找到ID为 {record_id} 的记录"
        })
    
    @mcp.tool()
    async def delete_record(table: str, record_id: int) -> str:
        """删除表中的记录（模拟）
        
        参数:
            table: 表名
            record_id: 记录ID
        """
        if table not in MOCK_DB:
            return json.dumps({"error": f"表不存在: {table}"})
        
        # 查找并删除记录
        for i, record in enumerate(MOCK_DB[table]):
            if record["id"] == record_id:
                MOCK_DB[table].pop(i)
                return json.dumps({
                    "success": True,
                    "message": f"记录 {record_id} 已删除"
                }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "success": False,
            "error": f"未找到ID为 {record_id} 的记录"
        })
    
    return mcp


# ============================================================================
# 练习4：天气Server（美国国家气象局API）
# ============================================================================

def create_weather_server():
    """天气查询MCP Server - 基于官方示例"""
    mcp = FastMCP("weather-server",port=8003)
    
    NWS_API_BASE = "https://api.weather.gov"
    USER_AGENT = "mcp-weather-server/1.0"
    
    async def make_nws_request(url: str) -> dict[str, Any] | None:
        """向NWS API发送请求并进行错误处理"""
        headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                return response.json()
            except Exception:
                return None
    
    def format_alert(feature: dict) -> str:
        """将警报特征格式化为可读字符串"""
        props = feature["properties"]
        return f"""
事件: {props.get("event", "未知")}
区域: {props.get("areaDesc", "未知")}
严重程度: {props.get("severity", "未知")}
描述: {props.get("description", "无描述")}
指示: {props.get("instruction", "无指示")}
"""
    
    @mcp.tool()
    async def get_alerts(state: str) -> str:
        """获取美国某州的天气警报
        
        参数:
            state: 两个字母的美国州代码（如 CA, NY）
        """
        url = f"{NWS_API_BASE}/alerts/active/area/{state}"
        data = await make_nws_request(url)
        
        if not data or "features" not in data:
            return "无法获取警报或未找到警报。"
        
        if not data["features"]:
            return f"{state}州当前没有活跃的天气警报。"
        
        alerts = [format_alert(feature) for feature in data["features"]]
        return "\n---\n".join(alerts)
    
    @mcp.tool()
    async def get_forecast(latitude: float, longitude: float) -> str:
        """获取某个位置的天气预报
        
        参数:
            latitude: 位置的纬度
            longitude: 位置的经度
        """
        # 首先获取预报网格端点
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)
        
        if not points_data:
            return "无法获取该位置的预报数据。"
        
        # 从points响应中获取预报URL
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = await make_nws_request(forecast_url)
        
        if not forecast_data:
            return "无法获取详细预报。"
        
        # 将时段格式化为可读的预报
        periods = forecast_data["properties"]["periods"]
        forecasts = []
        for period in periods[:5]:  # 显示接下来的5个时段
            forecast = f"""
{period["name"]}:
温度: {period["temperature"]}°{period["temperatureUnit"]}
风力: {period["windSpeed"]} {period["windDirection"]}
预报: {period["detailedForecast"]}
"""
            forecasts.append(forecast)
        
        return "\n---\n".join(forecasts)
    
    @mcp.prompt()
    async def weather_summary(city: str, state: str) -> str:
        """为美国城市生成天气摘要提示
        
        参数:
            city: 城市名称
            state: 两个字母的州代码
        """
        return f"""请为美国{state}州{city}市提供天气摘要。

使用 get_alerts 工具检查{state}州是否有任何活跃的天气警报。
如果您知道坐标，请使用 get_forecast 工具获取详细预报。

包含内容:
1. 当前警报（如有）
2. 温度和天气状况
3. 衣着和户外活动建议
"""
    
    return mcp


# ============================================================================
# 练习5：综合Server
# ============================================================================

def create_comprehensive_server():
    """综合MCP Server - Resources/Tools/Prompts"""
    mcp = FastMCP("comprehensive-server",port=8004)
    DATA_DIR = Path.home() / ".mcp_comprehensive"
    DATA_DIR.mkdir(exist_ok=True)
    
    @mcp.resource("doc://readme")
    async def get_readme() -> str:
        """获取服务器文档"""
        return """# 综合MCP Server

## 功能特性
- **save_data**: 保存数据到文件
- **analyze_data**: 分析已保存的数据
- **export_report**: 导出数据报告

## 使用示例
1. save_data("sales", {"q1": 100, "q2": 150, "q3": 200})
2. analyze_data("sales")
3. export_report("sales", "markdown")
"""
    
    @mcp.resource("data://{data_name}")
    async def get_data(data_name: str) -> str:
        """根据名称获取保存的数据
        
        参数:
            data_name: 数据的名称
        """
        data_file = DATA_DIR / f"{data_name}.json"
        if not data_file.exists():
            return json.dumps({"error": f"数据不存在: {data_name}"})
        
        with open(data_file, "r", encoding="utf-8") as f:
            return f.read()
    
    @mcp.tool()
    async def save_data(name: str, data: dict[str, Any]) -> str:
        """保存数据到文件
        
        参数:
            name: 数据的名称
            data: 要保存的数据字典
        """
        data_obj = {
            "name": name,
            "data": data,
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        data_file = DATA_DIR / f"{name}.json"
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data_obj, f, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "success": True,
            "name": name,
            "path": str(data_file)
        })
    
    @mcp.tool()
    async def analyze_data(data_name: str) -> str:
        """分析保存的数据并生成统计信息
        
        参数:
            data_name: 要分析的数据名称
        """
        data_file = DATA_DIR / f"{data_name}.json"
        if not data_file.exists():
            return json.dumps({"error": "数据不存在"})
        
        with open(data_file, "r", encoding="utf-8") as f:
            data_obj = json.load(f)
        
        data = data_obj.get("data", {})
        analysis = {
            "name": data_name,
            "type": type(data).__name__,
            "created_at": data_obj.get("created_at"),
            "analysis_time": datetime.now().isoformat()
        }
        
        if isinstance(data, dict):
            analysis["keys"] = list(data.keys())
            nums = [v for v in data.values() if isinstance(v, (int, float))]
            if nums:
                analysis["numeric_summary"] = {
                    "count": len(nums),
                    "min": min(nums),
                    "max": max(nums),
                    "sum": sum(nums),
                    "average": sum(nums) / len(nums)
                }
        
        return json.dumps(analysis, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    async def export_report(data_name: str, format: str = "json") -> str:
        """将数据导出为格式化报告
        
        参数:
            data_name: 数据名称
            format: 输出格式（json或markdown）
        """
        data_file = DATA_DIR / f"{data_name}.json"
        if not data_file.exists():
            return json.dumps({"error": "数据不存在"})
        
        with open(data_file, "r", encoding="utf-8") as f:
            data_obj = json.load(f)
        
        if format == "markdown":
            return f"""# {data_name} 数据报告

**创建时间**: {data_obj.get('created_at')}
**版本**: {data_obj.get('version')}

## 数据内容

```json
{json.dumps(data_obj.get('data'), ensure_ascii=False, indent=2)}
```

---
*报告生成时间: {datetime.now().isoformat()}*
"""
        else:
            return json.dumps(data_obj, ensure_ascii=False, indent=2)
    
    @mcp.prompt()
    async def data_analysis_prompt(data_name: str, focus: str = "general") -> str:
        """生成数据分析提示
        
        参数:
            data_name: 要分析的数据名称
            focus: 分析重点（trends、patterns、anomalies或general）
        """
        return f"""请分析名为"{data_name}"的数据。

步骤:
1. 使用 analyze_data 工具获取统计概览
2. 使用 data://{data_name} 资源访问完整数据
3. 执行详细分析
4. 总结关键发现

分析重点: {focus}

提供洞察、模式和建议。
"""
    
    return mcp


# ============================================================================
# 主程序 - 支持同时启动多个Server
# ============================================================================

# 全局进程列表
running_processes = []

def signal_handler(sig, frame):
    """处理Ctrl+C信号，优雅关闭所有Server"""
    print("\n\n⚠️  收到停止信号，正在关闭所有Server...")
    for process in running_processes:
        if process.is_alive():
            process.terminate()
    print("✅ 所有Server已关闭")
    sys.exit(0)


def start_server_process(server_name: str, server_func, port: int):
    """在独立进程中启动一个Server"""
    # 设置端口环境变量
    os.environ["PORT"] = str(port)
    
    print(f"  ✅ {server_name} 正在启动... (端口 {port})")
    
    # 创建并启动server
    mcp = server_func()
    mcp.run(transport="sse")


def main():
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    servers = {
        "1": ("文件Server", create_file_server, 8000),
        "2": ("笔记Server", create_note_server, 8001),
        "3": ("数据库Server", create_database_server, 8002),
        "4": ("天气Server", create_weather_server, 8003),
        "5": ("综合Server", create_comprehensive_server, 8004),
    }
    
    print("\n" + "=" * 60)
    print("MCP Server 启动器 (SSE模式) - 支持多Server")
    print("=" * 60)
    print("\n选择要启动的Server（可多选，用逗号分隔）：")
    print("  1. 文件Server      - 端口 8000")
    print("  2. 笔记Server      - 端口 8001")
    print("  3. 数据库Server    - 端口 8002")
    print("  4. 天气Server      - 端口 8003")
    print("  5. 综合Server      - 端口 8004")
    print("  all. 启动所有Server")
    print("\n" + "=" * 60)
    
    choice = input("\n请输入选项 (如: 1,2,3 或 all): ").strip()
    
    # 解析选择
    selected_servers = []
    if choice.lower() == "all":
        selected_servers = list(servers.keys())
    else:
        selected_servers = [c.strip() for c in choice.split(",") if c.strip() in servers]
    
    if not selected_servers:
        print("❌ 无效选项！")
        return
    
    print(f"\n{'=' * 60}")
    print(f"✅ 准备启动 {len(selected_servers)} 个Server")
    print(f"{'=' * 60}\n")
    
    # 启动选中的Servers
    for server_id in selected_servers:
        server_name, server_func, port = servers[server_id]
        
        # 创建进程
        process = Process(
            target=start_server_process,
            args=(server_name, server_func, port),
            name=f"MCP-{server_name}"
        )
        process.start()
        running_processes.append(process)
    
    print(f"\n{'=' * 60}")
    print(f"✅ 所有Server启动完成！")
    print(f"{'=' * 60}")
    print(f"\n运行中的Server:")
    for server_id in selected_servers:
        server_name, _, port = servers[server_id]
        print(f"  • {server_name:15s} - http://localhost:{port}/sse")
    
    print(f"\n⚠️  按 Ctrl+C 停止所有服务器")
    print(f"{'=' * 60}\n")
    
    # 等待所有进程
    try:
        for process in running_processes:
            process.join()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()


