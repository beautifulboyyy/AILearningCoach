"""
讲13 | MCP Client集成 - 实践练习

基于讲12中实现的5个MCP Server，完成Client端的集成练习：
1. 基础集成 - 创建简单的AI助手，集成文件Server
2. 多Server管理 - 同时连接文件Server和数据库Server
3. 智能工具调用 - 根据用户查询智能选择工具
4. Prompt应用 - 使用预定义模板进行分析
5. 完整应用 - 知识库问答系统

依赖：pip install mcp openai python-dotenv
运行：python 讲13-MCP Client集成.py

注意：需要先在另一个终端启动对应的MCP Server（讲12文件）
"""

import asyncio
import json
import os

from dotenv import load_dotenv

try:
    from mcp.client.sse import sse_client
    from mcp import ClientSession
    from openai import AsyncOpenAI
except ImportError:
    print("请先安装依赖: pip install mcp openai python-dotenv")
    raise

_ = load_dotenv()


# ============================================================================
# 练习1：基础集成 - 简单的AI助手集成文件Server
# ============================================================================

async def exercise1_basic_integration():
    """练习1：基础集成 - 简单的AI助手"""
    print("\n" + "=" * 70)
    print("练习1：基础集成 - 简单的AI助手集成文件Server")
    print("=" * 70 + "\n")

    server_url = "http://localhost:8000/sse"

    # 初始化LLM（如果可用）
    llm = None
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        llm = AsyncOpenAI()
        print("✅ LLM客户端初始化成功！\n")
    else:
        print("⚠️  未找到OPENAI_API_KEY，只能使用基础功能\n")

    try:
        print(f"🔌 正在连接到文件Server: {server_url}")

        # 使用标准的async with方式连接
        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ 文件Server连接成功！\n")

                # 列出并读取文件
                print("📁 搜索Python文件...")
                result = await session.call_tool("search_files", {"query": ".json"})
                data = json.loads(result.content[0].text)
                print(f"  找到 {data['count']} 个匹配的文件")

                if data['count'] > 0 and data['results']:
                    first_file = data['results'][0]
                    print(f"\n📖 读取文件: {first_file}\n")

                    try:
                        read_result = await session.read_resource(f"file://documents/{first_file}")
                        content = read_result.contents[0].text
                        print(f"文件内容预览:\n{content[:200]}...\n")
                    except Exception as e:
                        print(f"  ⚠️  读取失败: {e}\n")

                # 询问关于文件的问题
                if llm:
                    print("💬 用户问题: 有多少个json文件？\n")

                    result = await session.call_tool("list_files", {})
                    files_data = json.loads(result.content[0].text)

                    files_info = "\n".join([
                        f"- {f['name']} ({f['size']} bytes)"
                        for f in files_data.get('files', [])[:10]
                    ])

                    prompt = f"""你是一个文件助手。根据以下文件列表回答用户的问题。

文件列表:
{files_info}

用户问题: 有多少个Python文件？

请给出简洁明了的回答。"""

                    try:
                        response = await llm.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=300
                        )

                        answer = response.choices[0].message.content
                        print(f"🤖 AI助手回答:\n{answer}\n")
                    except Exception as e:
                        print(f"⚠️  LLM调用失败: {e}\n")

        print("🔌 已断开连接\n")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 练习2：多Server管理 - 文件Server + 数据库Server
# ============================================================================

async def exercise2_multi_server_manager():
    """练习2：多Server管理 - 同时管理文件Server和数据库Server"""
    print("\n" + "=" * 70)
    print("练习2：多Server管理 - 同时连接文件Server和数据库Server")
    print("=" * 70 + "\n")

    servers = {
        "文件Server": "http://localhost:8000/sse",
        "数据库Server": "http://localhost:8002/sse"
    }

    try:
        # 连接文件Server
        print(f"🔌 连接到文件Server...")
        async with sse_client(servers["文件Server"]) as (file_read, file_write):
            async with ClientSession(file_read, file_write) as file_session:
                await file_session.initialize()
                print("✅ 文件Server连接成功！\n")

                # 连接数据库Server
                print(f"🔌 连接到数据库Server...")
                async with sse_client(servers["数据库Server"]) as (db_read, db_write):
                    async with ClientSession(db_read, db_write) as db_session:
                        await db_session.initialize()
                        print("✅ 数据库Server连接成功！\n")

                        # 展示能力
                        print("\n📋 所有Server的能力列表：\n")

                        print("【文件Server】")
                        tools_result = await file_session.list_tools()
                        for tool in tools_result.tools[:3]:
                            print(f"  • {tool.name}: {tool.description}")
                        print()

                        print("【数据库Server】")
                        tools_result = await db_session.list_tools()
                        for tool in tools_result.tools[:3]:
                            print(f"  • {tool.name}: {tool.description}")
                        print()

                        # 跨Server操作
                        print("🔄 跨Server操作示例：\n")

                        # 从文件Server搜索文件
                        print("1️⃣ 使用文件Server搜索Python文件：")
                        result = await file_session.call_tool("search_files", {"query": ".py"})
                        data = json.loads(result.content[0].text)
                        print(f"   找到 {data['count']} 个Python文件\n")

                        # 从数据库Server查询数据
                        print("2️⃣ 使用数据库Server查询用户数据：")
                        result = await db_session.read_resource("db://table/users")
                        data = json.loads(result.contents[0].text)
                        print(f"   数据库中有 {data['count']} 个用户")
                        for user in data['rows'][:3]:
                            print(f"     • {user['name']}")
                        print()

        print("🔌 所有连接已断开\n")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 练习3：智能工具调用 - 根据用户查询智能选择和调用工具
# ============================================================================

async def exercise3_smart_tool_calling():
    """练习3：智能工具调用 - 根据用户查询智能选择工具"""
    print("\n" + "=" * 70)
    print("练习3：智能工具调用 - 根据用户查询智能选择和调用合适的工具")
    print("=" * 70 + "\n")

    server_url = "http://localhost:8001/sse"

    # 初始化LLM
    llm = None
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        llm = AsyncOpenAI()
        print("✅ LLM客户端初始化成功！\n")

    def rule_based_tool_selection(query: str) -> tuple[str, dict]:
        """基于规则的工具选择"""
        query_lower = query.lower()

        if "创建" in query or "新建" in query or "添加" in query:
            return "create_note", {}
        elif "搜索" in query or "查找" in query or "找" in query:
            return "search_notes", {}
        elif "列出" in query or "所有" in query or "全部" in query:
            return "list_notes", {}
        else:
            return "list_notes", {}

    async def llm_based_tool_selection(available_tools: dict, query: str) -> tuple[str, dict]:
        """基于LLM的智能工具选择"""
        tools_desc = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in available_tools.items()
        ])

        prompt = f"""你是一个工具选择助手。根据用户的查询，选择最合适的工具。

可用工具:
{tools_desc}

用户查询: {query}

请只返回工具名称，不要有其他内容。"""

        try:
            response = await llm.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )

            tool_name = response.choices[0].message.content.strip()
            return tool_name, {}

        except Exception as e:
            print(f"⚠️  LLM选择失败，使用规则匹配: {e}")
            return rule_based_tool_selection(query)

    try:
        print(f"🔌 连接到笔记Server: {server_url}")

        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ 笔记Server连接成功！\n")

                # 获取所有可用工具
                tools_result = await session.list_tools()
                available_tools = {}
                for tool in tools_result.tools:
                    available_tools[tool.name] = {
                        "description": tool.description,
                        "schema": tool.inputSchema
                    }

                # 先创建一些测试笔记
                print("📝 准备测试数据...\n")
                await session.call_tool("create_note", {
                    "title": "Python学习笔记",
                    "content": "学习了异步编程和MCP协议",
                    "tags": ["Python", "编程"]
                })
                await session.call_tool("create_note", {
                    "title": "项目计划",
                    "content": "下周要完成RAG系统的开发",
                    "tags": ["项目", "计划"]
                })
                print()

                # 测试不同的查询
                test_queries = [
                    "列出所有笔记",
                    "搜索关于Python的笔记",
                ]

                for query in test_queries:
                    print(f"💬 用户查询: {query}\n")

                    # 选择工具
                    if llm:
                        tool_name, params = await llm_based_tool_selection(available_tools, query)
                    else:
                        tool_name, params = rule_based_tool_selection(query)

                    print(f"🔧 选择的工具: {tool_name}\n")

                    # 处理特殊参数
                    if tool_name == "search_notes" and not params:
                        if "python" in query.lower():
                            params = {"query": "Python"}

                    # 调用工具
                    try:
                        result = await session.call_tool(tool_name, params)
                        response_text = result.content[0].text

                        # 格式化输出
                        try:
                            response_data = json.loads(response_text)
                            print(f"✅ 执行结果:")
                            print(json.dumps(response_data, ensure_ascii=False, indent=2))
                            print()
                        except:
                            print(f"✅ 执行结果:\n{response_text}\n")

                    except Exception as e:
                        print(f"❌ 工具调用失败: {e}\n")

                    print("-" * 70 + "\n")

        print("🔌 已断开连接\n")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 练习4：Prompt应用 - 使用预定义模板
# ============================================================================

async def exercise4_prompt_application():
    """练习4：Prompt应用 - 使用预定义模板进行分析"""
    print("\n" + "=" * 70)
    print("练习4：Prompt应用 - 使用预定义模板进行数据分析")
    print("=" * 70 + "\n")

    server_url = "http://localhost:8004/sse"

    # 初始化LLM
    llm = None
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        llm = AsyncOpenAI(api_key=api_key)
        print("✅ LLM客户端初始化成功！\n")

    try:
        print(f"🔌 连接到综合Server: {server_url}")

        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ 综合Server连接成功！\n")

                # 列出可用的Prompt
                print("📝 可用的Prompt模板：\n")
                result = await session.list_prompts()
                for prompt in result.prompts:
                    print(f"  • {prompt.name}")
                    print(f"    描述: {prompt.description}")
                print()

                print("=" * 70)
                print("使用Prompt模板进行数据分析")
                print("=" * 70 + "\n")

                # 1. 保存测试数据
                print("1️⃣ 保存测试数据...\n")
                await session.call_tool("save_data", {
                    "name": "monthly_sales",
                    "data": {
                        "January": 85000,
                        "February": 92000,
                        "March": 88000,
                        "April": 95000,
                        "May": 102000,
                        "June": 98000
                    }
                })

                # 2. 获取分析Prompt
                print("2️⃣ 获取数据分析Prompt模板...\n")
                prompt_result = await session.get_prompt("data_analysis_prompt", {
                    "data_name": "monthly_sales",
                    "focus": "trends"
                })

                prompt_text = prompt_result.messages[0].content.text
                print(f"生成的Prompt:\n{prompt_text}\n")
                print("-" * 70 + "\n")

                # 3. 获取数据内容
                print("3️⃣ 获取数据内容...\n")
                data_result = await session.read_resource("data://monthly_sales")
                data_content = data_result.contents[0].text

                # 4. 使用LLM进行分析
                if llm:
                    print("4️⃣ 使用LLM进行智能分析...\n")

                    full_prompt = f"{prompt_text}\n\n实际数据:\n{data_content}"

                    try:
                        response = await llm.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": full_prompt}],
                            max_tokens=500
                        )

                        analysis = response.choices[0].message.content
                        print(f"📊 分析结果:\n\n{analysis}\n")

                    except Exception as e:
                        print(f"⚠️  LLM分析失败: {e}\n")
                else:
                    print("⚠️  未配置LLM，使用基础分析工具...\n")
                    result = await session.call_tool("analyze_data", {"data_name": "monthly_sales"})
                    analysis = json.loads(result.content[0].text)
                    print(json.dumps(analysis, ensure_ascii=False, indent=2))
                    print()

        print("🔌 已断开连接\n")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 练习5：完整应用 - 知识库问答系统
# ============================================================================

async def exercise5_complete_application():
    """练习5：完整应用 - 知识库问答系统"""
    print("\n" + "=" * 70)
    print("练习5：完整应用 - 知识库问答系统")
    print("=" * 70 + "\n")

    server_url = "http://localhost:8001/sse"

    # 初始化LLM
    llm = None
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        llm = AsyncOpenAI(api_key=api_key)
        print("✅ LLM客户端初始化成功！\n")

    try:
        print(f"🔌 连接到笔记Server(知识库): {server_url}")

        async with sse_client(server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ 知识库连接成功！\n")

                # 初始化知识库
                print("📚 初始化知识库...\n")

                knowledge_items = [
                    {
                        "title": "Python异步编程",
                        "content": "Python的异步编程使用async/await语法。asyncio是Python的异步IO库，可以编写并发代码。异步编程特别适合IO密集型任务，如网络请求、文件读写等。",
                        "tags": ["Python", "异步编程", "asyncio"]
                    },
                    {
                        "title": "MCP协议介绍",
                        "content": "Model Context Protocol (MCP)是一个标准协议，允许AI模型访问外部工具和数据源。MCP定义了Resources、Tools和Prompts三种核心能力。它支持stdio和SSE两种传输方式。",
                        "tags": ["MCP", "协议", "AI"]
                    },
                    {
                        "title": "RAG系统架构",
                        "content": "RAG (Retrieval-Augmented Generation)系统结合了检索和生成。主要包括三个阶段：文档索引、相关文档检索、基于检索结果生成答案。RAG可以让LLM访问外部知识库。",
                        "tags": ["RAG", "AI", "架构"]
                    },
                ]

                for item in knowledge_items:
                    await session.call_tool("create_note", item)
                    print(f"  ✅ 已添加: {item['title']}")

                print("\n知识库初始化完成！\n")

                # 测试问答
                test_questions = [
                    "什么是MCP协议？",
                    "Python异步编程有什么特点？",
                ]

                for question in test_questions:
                    print("=" * 70)
                    print(f"💬 问题: {question}")
                    print("=" * 70 + "\n")

                    # 搜索相关知识
                    print(f"🔍 搜索知识库...\n")
                    result = await session.call_tool("search_notes", {"query": question})
                    data = json.loads(result.content[0].text)

                    print(f"  找到 {data['count']} 条相关知识\n")

                    if data['count'] == 0:
                        print("❌ 未找到相关知识\n")
                        continue

                    # 获取详细内容
                    print("📖 检索到的知识:\n")
                    knowledge_texts = []
                    for i, note in enumerate(data['results'][:3], 1):
                        note_id = note['id']
                        note_result = await session.read_resource(f"note://{note_id}")
                        note_data = json.loads(note_result.contents[0].text)

                        print(f"{i}. {note_data['title']}")
                        print(f"   {note_data['content'][:100]}...")
                        print()

                        knowledge_texts.append(f"知识{i}: {note_data['title']}\n{note_data['content']}")

                    # 使用LLM生成答案
                    if llm:
                        print("\n🤖 正在生成答案...\n")

                        context = "\n\n".join(knowledge_texts)
                        prompt = f"""你是一个知识库助手。基于以下知识回答用户的问题。

知识库内容:
{context}

用户问题: {question}

请基于知识库内容给出准确、详细的回答。"""

                        try:
                            response = await llm.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=400
                            )

                            answer = response.choices[0].message.content
                            print(f"📝 答案:\n{answer}\n")

                        except Exception as e:
                            print(f"⚠️  LLM调用失败: {e}\n")
                    else:
                        print("⚠️  未配置LLM，无法生成答案\n")

                    print("\n" + "=" * 70 + "\n")

        print("🔌 已断开连接\n")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 主程序
# ============================================================================

async def main():
    """主函数 - 运行所有练习"""

    print("\n" + "=" * 70)
    print("MCP Client集成 - 实践练习")
    print("=" * 70)

    exercises = {
        "1": ("基础集成 - 简单AI助手", exercise1_basic_integration),
        "2": ("多Server管理", exercise2_multi_server_manager),
        "3": ("智能工具调用", exercise3_smart_tool_calling),
        "4": ("Prompt应用", exercise4_prompt_application),
        "5": ("知识库问答系统", exercise5_complete_application),
        "all": ("运行所有练习", None),
    }

    print("\n请选择要运行的练习：")
    for key, (name, _) in exercises.items():
        print(f"  {key}. {name}")
    print()

    choice = input("请输入选项 (1-5/all): ").strip()

    if choice == "all":
        # 运行所有练习
        for key in ["1", "2", "3", "4", "5"]:
            _, exercise_func = exercises[key]
            try:
                await exercise_func()
                print("\n⏸️  暂停2秒...\n")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"\n❌ 练习{key}执行失败: {e}\n")
                import traceback
                traceback.print_exc()
                continue

    elif choice in exercises and choice != "all":
        _, exercise_func = exercises[choice]
        await exercise_func()

    else:
        print("❌ 无效选项！")
        return

    print("\n" + "=" * 70)
    print("✅ 练习完成！")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    print("""
⚠️  运行前准备：

1. 启动MCP Server
   在另一个终端运行: python 讲12-MCP Server开发.py
   根据要运行的练习选择对应的Server：
   - 练习1: 启动文件Server (选项1)
   - 练习2: 启动文件Server和数据库Server (需要分别启动)
   - 练习3: 启动笔记Server (选项2)
   - 练习4: 启动综合Server (选项5)
   - 练习5: 启动笔记Server (选项2)

2. 配置环境变量（可选，用于LLM智能功能）
   创建 .env 文件并添加: OPENAI_API_KEY=your_key_here

3. Server端口对应关系：
   - 文件Server:     http://localhost:8000/sse
   - 笔记Server:     http://localhost:8001/sse
   - 数据库Server:   http://localhost:8002/sse
   - 天气Server:     http://localhost:8003/sse
   - 综合Server:     http://localhost:8004/sse

4. 开始运行！
    """)

    asyncio.run(main())
