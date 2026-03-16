"""
讲06 | 高级Prompt技术 - 实践练习
使用DeepSeek API完成所有练习

环境准备:
pip install openai python-dotenv

设置API Key:
在.env文件中添加: DEEPSEEK_API_KEY=your_key_here
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# DeepSeek API配置
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

if not API_KEY:
    print("⚠️  请设置DEEPSEEK_API_KEY环境变量")
    print("   在.env文件中添加: DEEPSEEK_API_KEY=your_key_here")


def print_section(title: str):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_subsection(title: str):
    """打印子章节标题"""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70 + "\n")


client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ============================================================================
# 练习1：理解ReAct基础流程
# ============================================================================

def exercise_1_react_weather():
    """
    练习1：用ReAct模式查询北京天气
    
    要求：
    - 理解Thought（思考）→ Action（行动）→ Observation（观察）的循环
    - 手动模拟2-3轮循环
    - 不需要真实工具调用，用文字描述即可
    """
    print_section("练习1：理解ReAct基础流程")
    
    print("📝 任务：查询北京明天的天气\n")
    
    prompt = """请用ReAct模式完成以下任务：查询北京明天的天气

请严格按照以下格式输出（模拟2-3轮循环）：

Thought 1: [分析：我需要做什么？为什么这样做？]
Action 1: [描述：我要执行什么行动？]
Observation 1: [模拟结果：假设这个行动的返回结果是什么？]

Thought 2: [基于Observation 1的思考]
Action 2: [下一步行动]
Observation 2: [模拟结果]

Thought 3: [最终思考]
Action 3: [最终行动，如"回复用户"]
Final Answer: [给用户的最终答案]

注意：
- Thought要说明为什么这样做
- Action要具体描述行动
- Observation要合理模拟结果
- 最后要给出Final Answer"""
    
    print("🤖 发送Prompt给LLM...")
    print(f"Prompt:\n{prompt}\n")
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        result = response.choices[0].message.content
        print("✅ LLM回复：")
        print(result)
        print("\n")
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        print("\n💡 参考答案示例：")
        print("""
Thought 1: 用户想知道北京明天的天气，我需要调用天气查询API获取信息
Action 1: 调用天气API，参数为city="北京", date="明天"
Observation 1: API返回：北京明天晴转多云，气温15-25°C，风力3级

Thought 2: 已经获取到天气信息，现在需要以友好的方式呈现给用户
Action 2: 整理信息，格式化输出
Observation 2: 信息已整理完成

Thought 3: 信息已准备好，可以回复用户了
Action 3: 回复用户
Final Answer: 北京明天天气：晴转多云，气温15-25°C，风力3级。建议穿长袖衬衫，适合出行。
        """)
    
    print_subsection("🎯 练习1总结")
    print("""
ReAct = Reasoning（推理）+ Acting（行动）

核心循环：
1. Thought（思考）：分析当前状况，决定下一步做什么
2. Action（行动）：执行具体的操作（如调用工具、查询信息）
3. Observation（观察）：获取行动的结果
4. 重复1-3，直到完成任务

与普通Prompt的区别：
- ❌ 普通：直接问"北京明天天气？" → 模型凭记忆回答（可能过时）
- ✅ ReAct：思考 → 查询工具 → 观察结果 → 回答（实时准确）

适用场景：
- 需要实时信息的任务（天气、股票、新闻）
- 需要多步骤推理的任务
- 需要调用外部工具的任务
    """)


# ============================================================================
# 练习2：尝试Tree of Thoughts
# ============================================================================

def exercise_2_tot_learning():
    """
    练习2：用ToT方法为"如何提高学习效率"生成3个不同思路
    
    要求：
    - 生成3个不同角度的想法
    - 对每个想法简单打分（1-5分）
    - 选择最优的一个稍微展开
    """
    print_section("练习2：尝试Tree of Thoughts")
    
    print("📝 问题：如何提高学习效率？\n")
    
    # 步骤1：生成3个思路
    prompt_step1 = """请为"如何提高学习效率"这个问题生成3个不同的解决思路。

要求：
- 思路1：从时间管理角度思考
- 思路2：从学习方法角度思考  
- 思路3：从环境优化角度思考

请输出3个思路，每个思路用2-3句话描述。"""
    
    print_subsection("步骤1：生成3个不同思路")
    print(f"Prompt:\n{prompt_step1}\n")
    
    try:
        response1 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt_step1}],
            temperature=0.8  # 提高温度以获得更多样的思路
        )
        
        thoughts = response1.choices[0].message.content
        print("✅ 生成的思路：")
        print(thoughts)
        print("\n")
        
        # 步骤2：打分评估
        prompt_step2 = f"""现在请对这3个思路打分（1-5分），评估它们的可行性和效果。

刚才生成的思路：
{thoughts}

请按以下格式输出：

思路1评分: [X分] 理由: [为什么给这个分数]
思路2评分: [X分] 理由: [为什么给这个分数]
思路3评分: [X分] 理由: [为什么给这个分数]

然后说明哪个思路得分最高。"""
        
        print_subsection("步骤2：对思路打分（1-5分）")
        print(f"Prompt:\n{prompt_step2}\n")
        
        response2 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt_step1},
                {"role": "assistant", "content": thoughts},
                {"role": "user", "content": prompt_step2}
            ],
            temperature=0.3  # 降低温度以获得更客观的评估
        )
        
        scores = response2.choices[0].message.content
        print("✅ 评分结果：")
        print(scores)
        print("\n")
        
        # 步骤3：展开最优思路
        prompt_step3 = """基于上述评分，请选择得分最高的思路，展开3-5个具体的行动建议。

格式：
最优思路：[思路名称]
具体建议：
1. ...
2. ...
3. ..."""
        
        print_subsection("步骤3：展开最优思路")
        print(f"Prompt:\n{prompt_step3}\n")
        
        response3 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt_step1},
                {"role": "assistant", "content": thoughts},
                {"role": "user", "content": prompt_step2},
                {"role": "assistant", "content": scores},
                {"role": "user", "content": prompt_step3}
            ],
            temperature=0.5
        )
        
        expansion = response3.choices[0].message.content
        print("✅ 展开的建议：")
        print(expansion)
        print("\n")
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        print("\n💡 参考答案示例：")
        print("""
【步骤1 - 生成思路】
思路1（时间管理）：使用番茄工作法，将学习时间分成25分钟的专注块，中间休息5分钟，提高专注度。
思路2（学习方法）：采用费曼学习法，通过向他人解释来检验理解程度，发现知识盲区。
思路3（环境优化）：创建专门的学习空间，减少干扰源，使用白噪音提升专注力。

【步骤2 - 打分】
思路1评分: 4分 理由: 番茄工作法简单易行，科学有效，但需要自律
思路2评分: 5分 理由: 费曼学习法能深度理解知识，效果最好
思路3评分: 3分 理由: 环境改善有帮助，但不是核心因素

【步骤3 - 展开】
最优思路：思路2（费曼学习法）
具体建议：
1. 学习新概念后，用自己的话写下来或讲给别人听
2. 遇到卡壳的地方，记录下来重点复习
3. 尝试用类比和例子来解释复杂概念
4. 定期复述之前学过的内容，巩固记忆
        """)
    
    print_subsection("🎯 练习2总结")
    print("""
Tree of Thoughts (ToT) = 思维树

核心思想：
- 像下棋一样，探索多个可能的解决路径
- 评估每条路径的优劣
- 选择最优路径深入探索

与普通Prompt的区别：
- ❌ 普通：直接问"如何提高学习效率？" → 得到一个答案
- ✅ ToT：生成多个思路 → 评估打分 → 选择最优 → 展开

适用场景：
- 开放性问题（如何提升、如何优化）
- 创意策划（活动方案、营销策略）
- 决策分析（选择A还是B）
- 问题解决（故障排查、方案设计）
    """)


# ============================================================================
# 练习3：Self-Refine简单应用
# ============================================================================

def exercise_3_self_refine_apology():
    """
    练习3：写一封客户道歉邮件，用Self-Refine改进一次
    
    步骤：
    1. 第一轮：直接生成初版邮件
    2. 第二轮：从3个维度自我评估（礼貌性、清晰度、解决方案）
    3. 第三轮：根据评估改进
    """
    print_section("练习3：Self-Refine简单应用")
    
    print("📝 场景：订单延迟发货，需要给客户道歉\n")
    
    # 第一轮：生成初版
    prompt_round1 = """场景：客户订购的商品因为物流问题延迟了3天发货，需要写一封道歉邮件。

客户信息：
- 客户姓名：张先生
- 订单号：20240115001
- 商品：智能手表
- 原定发货时间：1月12日
- 实际发货时间：1月15日

请写一封道歉邮件（150-200字），要有诚意，并给出补偿方案。"""
    
    print_subsection("第一轮：生成初版邮件")
    print(f"Prompt:\n{prompt_round1}\n")
    
    try:
        response1 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt_round1}],
            temperature=0.7
        )
        
        draft_v1 = response1.choices[0].message.content
        print("✅ 初版邮件：")
        print(draft_v1)
        print("\n")
        
        # 第二轮：自我评估
        prompt_round2 = """请对上面的道歉邮件进行自我评估，从3个维度打分（每项满分5分）：

1. 礼貌性（是否足够真诚、有礼貌）
2. 清晰度（延迟原因和补偿方案是否说清楚）
3. 解决方案（补偿是否合理、令人满意）

请按以下格式输出：

礼貌性: [X/5分] 问题: [指出存在的问题]
清晰度: [X/5分] 问题: [指出存在的问题]
解决方案: [X/5分] 问题: [指出存在的问题]

总分: [XX/15分]

主要需要改进的地方：
1. ...
2. ...
3. ..."""
        
        print_subsection("第二轮：自我评估（3个维度打分）")
        print(f"Prompt:\n{prompt_round2}\n")
        
        response2 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt_round1},
                {"role": "assistant", "content": draft_v1},
                {"role": "user", "content": prompt_round2}
            ],
            temperature=0.3  # 降低温度以获得更客观的评估
        )
        
        evaluation = response2.choices[0].message.content
        print("✅ 评估结果：")
        print(evaluation)
        print("\n")
        
        # 第三轮：改进
        prompt_round3 = """基于上述评估，请重写这封道歉邮件，针对指出的问题进行改进。

要求：
- 保持150-200字
- 针对每个评分低的维度进行优化
- 更加真诚和专业"""
        
        print_subsection("第三轮：改进版邮件")
        print(f"Prompt:\n{prompt_round3}\n")
        
        response3 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt_round1},
                {"role": "assistant", "content": draft_v1},
                {"role": "user", "content": prompt_round2},
                {"role": "assistant", "content": evaluation},
                {"role": "user", "content": prompt_round3}
            ],
            temperature=0.7
        )
        
        draft_v2 = response3.choices[0].message.content
        print("✅ 改进后的邮件：")
        print(draft_v2)
        print("\n")
        
        # 对比
        print_subsection("版本对比")
        print("【初版】")
        print(draft_v1)
        print("\n【改进版】")
        print(draft_v2)
        print("\n")
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        print("\n💡 参考答案示例：")
        print("""
【初版】
尊敬的张先生，您好！很抱歉您的订单延迟发货了。由于物流原因，您的智能手表晚了3天发货。我们会尽快配送。作为补偿，我们给您50元优惠券。

【评估】
礼貌性: 3/5分 问题: 道歉不够真诚，没有表达充分歉意
清晰度: 3/5分 问题: "物流原因"太笼统，没说清楚具体原因
解决方案: 2/5分 问题: 50元优惠券对于3天延迟不够有诚意

【改进版】
尊敬的张先生：

非常抱歉！您订购的智能手表（订单号20240115001）因春节期间快递运力紧张延迟了3天发货，原定1月12日发货，实际1月15日才发出。我们深知这给您带来了不便。

为表歉意，我们将为您：
1. 升级为顺丰次日达（免运费）
2. 赠送100元现金券（无门槛）
3. 订单金额的10%作为补偿金

再次诚挚道歉，感谢您的理解！

XX电商客服团队
        """)
    
    print_subsection("🎯 练习3总结")
    print("""
Self-Refine = 自我优化

核心流程：
1. 生成初版内容
2. 自我评估（找问题、打分）
3. 基于评估改进
4. （可选）重复2-3直到满意

与普通Prompt的区别：
- ❌ 普通：生成一次就完事，质量全靠运气
- ✅ Self-Refine：生成 → 评估 → 改进，持续提升质量

适用场景：
- 文案写作（邮件、文章、广告）
- 代码优化（发现bug、改进性能）
- 方案设计（找漏洞、完善细节）
- 内容审核（检查错误、提升质量）

关键要点：
- 评估要有明确标准（如3个维度、5分制）
- 评估要客观，真正找出问题
- 改进要针对性地解决评估中发现的问题
    """)


# ============================================================================
# 练习4：Prompt Chain入门
# ============================================================================

def exercise_4_prompt_chain_food():
    """
    练习4：为"写一篇美食推荐"设计3步Prompt链
    
    要求：
    - 设计3个连续的Prompt
    - 每一步的输出是下一步的输入
    - 体会任务分解的好处
    """
    print_section("练习4：Prompt Chain入门")
    
    print("📝 任务：写一篇美食推荐\n")
    
    # Step 1: 选择美食类型和特点
    prompt_step1 = """请推荐一种适合冬天吃的美食，说明它的特点。

要求：
- 适合冬天
- 有营养
- 做法相对简单
- 用2-3句话描述"""
    
    print_subsection("Step 1: 选择美食类型和特点")
    print(f"Prompt:\n{prompt_step1}\n")
    
    try:
        response1 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt_step1}],
            temperature=0.7
        )
        
        step1_output = response1.choices[0].message.content
        print("✅ Step 1 输出：")
        print(step1_output)
        print("\n")
        
        # Step 2: 生成详细介绍
        prompt_step2 = f"""基于以下美食信息，写一段200字左右的详细介绍，包括口味、做法、营养价值。

美食信息：
{step1_output}

请写一段美食介绍（200字左右）："""
        
        print_subsection("Step 2: 生成详细介绍")
        print(f"Prompt:\n{prompt_step2}\n")
        
        response2 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt_step1},
                {"role": "assistant", "content": step1_output},
                {"role": "user", "content": prompt_step2}
            ],
            temperature=0.7
        )
        
        step2_output = response2.choices[0].message.content
        print("✅ Step 2 输出：")
        print(step2_output)
        print("\n")
        
        # Step 3: 添加推荐理由
        prompt_step3 = f"""基于上述美食介绍，补充说明为什么推荐这道美食，适合什么人群。

之前的介绍：
{step2_output}

请补充推荐理由和适合人群（100字左右）："""
        
        print_subsection("Step 3: 添加推荐理由")
        print(f"Prompt:\n{prompt_step3}\n")
        
        response3 = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt_step1},
                {"role": "assistant", "content": step1_output},
                {"role": "user", "content": prompt_step2},
                {"role": "assistant", "content": step2_output},
                {"role": "user", "content": prompt_step3}
            ],
            temperature=0.7
        )
        
        step3_output = response3.choices[0].message.content
        print("✅ Step 3 输出：")
        print(step3_output)
        print("\n")
        
        # 展示完整结果
        print_subsection("🎨 完整的美食推荐文章")
        print(f"{step1_output}\n\n{step2_output}\n\n{step3_output}")
        print("\n")
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        print("\n💡 参考答案示例：")
        print("""
【Step 1 输出】
推荐：羊肉炖萝卜。这道菜温补暖身，特别适合冬天食用。羊肉富含蛋白质，萝卜帮助消化，两者搭配营养均衡。做法简单，炖煮即可。

【Step 2 输出】
羊肉炖萝卜是一道经典的冬季滋补菜肴。选用新鲜的羊腿肉，切块后焯水去腥，配上白萝卜块，加入姜片、料酒、盐和少许花椒。小火慢炖1.5-2小时，直到羊肉软烂，萝卜入味。

口味上，羊肉鲜香浓郁，萝卜吸收了肉汁的精华，清甜可口，汤汁醇厚。营养价值方面，羊肉富含优质蛋白质、铁元素和维生素B族，能够温补脾胃、益气补血；白萝卜富含维生素C和膳食纤维，有助于消化，正好解羊肉的油腻。

【Step 3 输出】
推荐理由：冬季寒冷，人体需要补充热量和营养，羊肉炖萝卜正是最佳选择。这道菜不仅能驱寒保暖，还能增强免疫力。做法简单，食材易得，适合家庭制作。

适合人群：特别适合怕冷体质、气血不足的人群；也适合老人和儿童，因为炖得软烂易消化；工作压力大、容易疲劳的上班族也可以常吃来补充体力。但需注意，上火体质和高血压患者应适量食用。
        """)
    
    print_subsection("🎯 练习4总结")
    print("""
Prompt Chain = 提示词链

核心思想：
- 将复杂任务分解成多个简单步骤
- 每一步的输出作为下一步的输入
- 像流水线一样，逐步完成任务

任务分解：
复杂任务 → Step 1 → Step 2 → Step 3 → 最终结果

与一次性生成的对比：
- ❌ 一次性：让LLM直接写完整文章，可能结构混乱、遗漏内容
- ✅ Chain：分步骤生成，每步都有明确目标，质量更可控

适用场景：
- 长文档写作（文章、报告、方案）
- 复杂流程（数据分析：收集→清洗→分析→可视化）
- 创意项目（从概念到成品）
- 软件开发（需求→设计→实现→测试）

关键要点：
- 每个步骤要有明确的输入和输出
- 步骤之间要有逻辑关系
- 可以在任何步骤介入调整
- 步骤不要太细（3-5步最佳）
    """)


# ============================================================================
# 练习5：选择一个技术深入练习
# ============================================================================

def exercise_5_choose_technique():
    """
    练习5：选择一个技术深入练习
    
    要求：
    - 从ReAct、ToT、Self-Refine、Prompt Chain中选择一个
    - 设计一个实际应用场景
    - 用LLM测试效果
    """
    print_section("练习5：选择一个技术深入练习")
    
    print("""
📚 请从以下技术中选择一个你最感兴趣的：

1. ReAct（推理+行动）
   - 适合场景：客服问答、信息查询、需要调用工具的任务
   - 核心：Thought → Action → Observation 循环

2. ToT（思维树）
   - 适合场景：创意策划、问题解决、决策分析
   - 核心：生成多个思路 → 评估 → 选择最优

3. Self-Refine（自我优化）
   - 适合场景：文案写作、代码优化、内容审核
   - 核心：生成 → 评估 → 改进

4. Prompt Chain（提示词链）
   - 适合场景：复杂报告生成、数据分析流程
   - 核心：任务分解 → 逐步完成

请输入你的选择（1-4）：""")
    
    try:
        choice = input().strip()
        
        if choice == "1":
            demonstrate_react()
        elif choice == "2":
            demonstrate_tot()
        elif choice == "3":
            demonstrate_self_refine()
        elif choice == "4":
            demonstrate_prompt_chain()
        else:
            print("\n⚠️  无效选择，展示所有技术的应用场景示例...")
            show_all_examples()
            
    except Exception as e:
        print(f"\n提示：这是一个交互式练习，你可以：")
        print("1. 选择一个你感兴趣的技术")
        print("2. 想一个你工作/学习中的实际场景")
        print("3. 设计Prompt并用ChatGPT/Claude/DeepSeek测试")
        print("4. 记录效果和改进建议\n")
        show_all_examples()


def demonstrate_react():
    """演示ReAct的应用"""
    print_subsection("ReAct技术演示")
    
    print("""
🎯 场景示例：智能客服回答用户问题

假设用户问："我的订单ORD12345什么时候能到？"

ReAct流程：

Thought 1: 用户询问订单状态，我需要查询订单系统
Action 1: 调用订单查询API，参数order_id="ORD12345"
Observation 1: 订单状态=已发货，快递单号=SF1234567890，预计1月20日送达

Thought 2: 订单已发货，我再查询一下物流详情
Action 2: 调用物流查询API，参数tracking_number="SF1234567890"
Observation 2: 当前位置=本地派件中，配送员王师傅，电话138****5678

Thought 3: 信息已收集完整，可以回复用户了
Action 3: 整理信息，生成友好的回复
Final Answer: 您好！您的订单ORD12345已经在配送中了，预计今天（1月20日）就能送达。配送员王师傅（138****5678）稍后会联系您确认收货时间。

💡 你的实践任务：
1. 想一个需要查询信息的场景（如查天气、查股票、查航班）
2. 设计3轮ReAct循环
3. 用LLM测试效果
4. 思考：如果没有真实工具，如何模拟？
    """)


def demonstrate_tot():
    """演示ToT的应用"""
    print_subsection("ToT技术演示")
    
    print("""
🎯 场景示例：为公司年会策划活动方案

Step 1 - 生成3个思路：
思路1（传统晚会）：租酒店、请主持人、节目表演、抽奖
思路2（团建活动）：户外拓展、团队游戏、烧烤聚餐
思路3（创意派对）：主题化装、互动游戏、才艺秀

Step 2 - 评估打分：
思路1: 4分 - 正式但略显传统
思路2: 3分 - 轻松但天气限制大
思路3: 5分 - 有趣且参与度高

Step 3 - 展开最优思路（创意派对）：
1. 主题：复古80年代
2. 着装：鼓励80年代服装
3. 活动：经典游戏（踢毽子、跳房子）+ 卡拉OK
4. 餐饮：怀旧小吃（大白兔奶糖、北冰洋汽水）
5. 奖品：定制复古徽章、纪念品

💡 你的实践任务：
1. 想一个需要创意的问题（如营销方案、生日惊喜、旅行计划）
2. 生成3个不同角度的思路
3. 评估并选择最优
4. 思考：如何确保思路真的不同？
    """)


def demonstrate_self_refine():
    """演示Self-Refine的应用"""
    print_subsection("Self-Refine技术演示")
    
    print("""
🎯 场景示例：优化一段产品描述文案

初版文案：
"这款笔记本电脑很好用，性能强，屏幕大，价格便宜。"

评估（满分5分）：
- 专业性: 2/5 - 用词太口语化
- 吸引力: 2/5 - 没有亮点和细节
- 说服力: 1/5 - 缺少具体数据

改进版文案：
"轻薄本新标杆：14英寸2.8K视网膜屏，搭载M2芯片（8核CPU+10核GPU），16GB内存+512GB固态硬盘，续航长达18小时。原价9999元，限时优惠价7999元，立省2000元！"

对比：
✅ 用专业术语替代口语（"性能强"→"M2芯片"）
✅ 用具体数据支撑（"屏幕大"→"14英寸2.8K"）
✅ 强化价格优势（"便宜"→"立省2000元"）

💡 你的实践任务：
1. 写一段文案（产品介绍、自我介绍、活动宣传）
2. 从3个维度评估（如专业性、吸引力、说服力）
3. 基于评估改进
4. 思考：如何让评估更客观？
    """)


def demonstrate_prompt_chain():
    """演示Prompt Chain的应用"""
    print_subsection("Prompt Chain技术演示")
    
    print("""
🎯 场景示例：写一份市场分析报告

Chain流程：

Step 1: 市场概况
输入：行业名称（如"在线教育"）
输出：市场规模、增长率、主要玩家

Step 2: 竞争分析
输入：Step 1的输出 + 我们的产品
输出：竞品对比表、我们的优劣势

Step 3: 机会与挑战
输入：Step 1和2的输出
输出：SWOT分析、市场机会点

完整报告 = Step 1 + Step 2 + Step 3

示例输出：
【市场概况】在线教育市场规模达5000亿...
【竞争分析】主要竞品包括A公司、B公司...
【机会与挑战】我们的机会在于...

💡 你的实践任务：
1. 选择一个需要多步骤的任务（如写简历、策划方案、数据分析）
2. 分解成3-4个步骤
3. 设计每步的Prompt
4. 思考：步骤之间如何传递信息？
    """)


def show_all_examples():
    """展示所有技术的示例"""
    print_subsection("📖 四种技术应用场景速查")
    
    print("""
1️⃣ ReAct（推理+行动）- 需要多步骤查询
   ✅ 客服回答："订单何时到？" → 查订单 → 查物流 → 回复
   ✅ 旅行规划："去北京玩" → 查景点 → 查天气 → 查住宿 → 出方案
   ✅ 股票分析："推荐股票" → 查行情 → 查财报 → 分析 → 推荐

2️⃣ ToT（思维树）- 需要探索多个方案
   ✅ 营销策划：想3个活动创意 → 评估 → 选最优 → 细化
   ✅ 问题解决："转化率低" → 想3个原因 → 评估 → 选主因 → 解决
   ✅ 决策分析："选A还是B" → 列优缺点 → 打分 → 做决策

3️⃣ Self-Refine（自我优化）- 需要提升质量
   ✅ 文案写作：写文案 → 评估 → 改进 → 再评估
   ✅ 代码优化：写代码 → 找bug → 修复 → 优化性能
   ✅ 简历修改：写简历 → 评估亮点 → 优化 → 定稿

4️⃣ Prompt Chain（提示词链）- 复杂任务分解
   ✅ 论文写作：大纲 → 文献综述 → 方法 → 结果 → 结论
   ✅ 项目规划：需求分析 → 方案设计 → 任务分解 → 时间表
   ✅ 数据分析：收集数据 → 清洗 → 分析 → 可视化 → 报告

💡 实践建议：
1. 从简单场景开始（如查天气、写邮件）
2. 用ChatGPT/Claude/DeepSeek实际测试
3. 记录效果，总结经验
4. 逐步应用到工作/学习中
    """)


def main():
    """主函数"""
    import sys
    
    print_section("讲06 | 高级Prompt技术 - 简化版实践练习")
    print("""
本练习包含5个简化版任务，帮助你快速理解高级Prompt技术：

1. 练习1：理解ReAct基础流程（手动模拟2-3轮）
2. 练习2：尝试Tree of Thoughts（生成3个思路并打分）
3. 练习3：Self-Refine简单应用（写邮件并改进一次）
4. 练习4：Prompt Chain入门（3步链式生成）
5. 练习5：选择一个技术深入练习（实际应用）
    """)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("\n请选择要运行的练习（1-5，或输入 all 运行全部）：")
        choice = input().strip()
    
    if choice == "1":
        exercise_1_react_weather()
    elif choice == "2":
        exercise_2_tot_learning()
    elif choice == "3":
        exercise_3_self_refine_apology()
    elif choice == "4":
        exercise_4_prompt_chain_food()
    elif choice == "5":
        exercise_5_choose_technique()
    elif choice == "all" or choice == "":
        print("\n🚀 开始运行所有练习...\n")
        exercise_1_react_weather()
        input("\n按回车继续下一个练习...")
        exercise_2_tot_learning()
        input("\n按回车继续下一个练习...")
        exercise_3_self_refine_apology()
        input("\n按回车继续下一个练习...")
        exercise_4_prompt_chain_food()
        input("\n按回车继续下一个练习...")
        exercise_5_choose_technique()
        print("\n\n🎉 所有练习完成！")
    else:
        print(f"\n⚠️  无效选项：{choice}")
        print("\n使用方法：python 讲06-高级Prompt.py [选项]\n")
        print("选项说明：")
        print("  1   - 练习1：理解ReAct基础流程")
        print("  2   - 练习2：尝试Tree of Thoughts")
        print("  3   - 练习3：Self-Refine简单应用")
        print("  4   - 练习4：Prompt Chain入门")
        print("  5   - 练习5：选择一个技术深入练习")
        print("  all - 运行所有练习（默认）")
        print("\n示例：python 讲06-高级Prompt.py 1")


if __name__ == "__main__":
    main()
