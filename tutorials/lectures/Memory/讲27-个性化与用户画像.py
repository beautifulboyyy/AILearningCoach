"""
讲27｜个性化与用户画像 - 实战案例：个性化AI学习助手

本案例展示如何构建一个能够根据学生学习风格提供个性化教学的AI助手。

核心功能：
1. 用户画像构建 - 从对话中提取学生特征
2. 偏好学习 - 显式询问 + 隐式推断
3. 个性化教学 - 根据画像调整教学方式
4. 效果追踪 - 记录和评估个性化效果

技术栈：
- LLM: DeepSeek-Chat (通过OpenAI兼容接口)
- 记忆系统: mem0
- API: https://api.deepseek.com

运行前准备：
1. 确保.env文件中配置了DEEPSEEK_API_KEY
2. 安装依赖: pip install openai mem0ai python-dotenv
"""

from openai import OpenAI
from mem0 import Memory
import os
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

# 配置DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = "deepseek-chat"  # DeepSeek的对话模型

class StudentProfile:
    """学生画像类"""
    
    def __init__(self, student_id):
        self.student_id = student_id
        self.basic_info = {
            "goal": None,  # 学习目标: beginner/intermediate/advanced
            "background": None,  # 知识背景: none/some/expert
            "time_available": None  # 可用时间: limited/moderate/plenty
        }
        self.learning_style = {
            "type": None,  # 学习类型: practical/theoretical/balanced
            "pace": None,  # 节奏: fast/moderate/slow
            "detail_level": None  # 详细程度: concise/balanced/detailed
        }
        self.behaviors = {
            "question_frequency": 0,  # 提问频率
            "skip_theory_count": 0,  # 跳过理论次数
            "code_view_time": 0,  # 代码查看时长
            "theory_view_time": 0  # 理论阅读时长
        }
    
    def update_from_explicit(self, preference_type, value):
        """更新显式偏好"""
        if preference_type == "learning_style":
            self.learning_style["type"] = value
        elif preference_type == "pace":
            self.learning_style["pace"] = value
        elif preference_type == "detail":
            self.learning_style["detail_level"] = value
    
    def update_from_implicit(self, behavior_data):
        """从行为数据更新隐式偏好"""
        # 更新行为统计
        for key, value in behavior_data.items():
            if key in self.behaviors:
                self.behaviors[key] += value
        
        # 推断学习类型
        if self.behaviors["skip_theory_count"] > 5:
            self.learning_style["type"] = "practical"
        elif self.behaviors["theory_view_time"] > self.behaviors["code_view_time"] * 2:
            self.learning_style["type"] = "theoretical"
        else:
            self.learning_style["type"] = "balanced"
        
        # 推断节奏
        if self.behaviors["question_frequency"] > 10:
            self.learning_style["pace"] = "fast"
    
    def get_summary(self):
        """获取画像摘要"""
        return {
            "student_id": self.student_id,
            "learning_style": self.learning_style["type"] or "未知",
            "pace": self.learning_style["pace"] or "适中",
            "detail_level": self.learning_style["detail_level"] or "平衡"
        }


class PersonalizedTeachingAssistant:
    """个性化教学助手"""
    
    def __init__(self):
        # 使用DeepSeek API
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        self.memory = Memory()
        self.profiles = {}  # 存储学生画像
    
    def initialize_student(self, student_id):
        """初始化学生并收集显式偏好"""
        print(f"\n=== 欢迎新学生: {student_id} ===\n")
        
        # 创建画像
        profile = StudentProfile(student_id)
        
        # 显式偏好收集
        print("为了提供更好的学习体验,请回答几个问题:\n")
        
        # 问题1: 学习风格
        print("1. 你更喜欢哪种学习方式?")
        print("   A. 快速上手,边做边学(实践型)")
        print("   B. 系统学习,理解原理(理论型)")
        print("   C. 两者结合(平衡型)")
        style = input("请选择 (A/B/C): ").strip().upper()
        
        style_map = {"A": "practical", "B": "theoretical", "C": "balanced"}
        profile.learning_style["type"] = style_map.get(style, "balanced")
        
        # 问题2: 学习节奏
        print("\n2. 你希望的学习节奏是?")
        print("   A. 快速(快速掌握要点)")
        print("   B. 适中(稳步推进)")
        print("   C. 慢速(深入理解)")
        pace = input("请选择 (A/B/C): ").strip().upper()
        
        pace_map = {"A": "fast", "B": "moderate", "C": "slow"}
        profile.learning_style["pace"] = pace_map.get(pace, "moderate")
        
        # 保存画像
        self.profiles[student_id] = profile
        
        # 保存到记忆系统
        self._save_preference(student_id, f"学习风格: {profile.learning_style['type']}")
        self._save_preference(student_id, f"学习节奏: {profile.learning_style['pace']}")
        
        print(f"\n✅ 画像已创建! 学习风格: {profile.learning_style['type']}, 节奏: {profile.learning_style['pace']}\n")
        
        return profile
    
    def teach_concept(self, student_id, concept_name):
        """根据学生画像教授概念"""
        profile = self.profiles.get(student_id)
        
        if not profile:
            print("学生画像不存在,请先初始化")
            return
        
        print(f"\n=== 教授概念: {concept_name} ===\n")
        
        # 根据学习风格生成个性化教学内容
        teaching_content = self._generate_personalized_content(
            concept_name, 
            profile.learning_style["type"]
        )
        
        print(teaching_content)
        
        # 记录本次教学
        self._save_interaction(student_id, f"学习了{concept_name}")
    
    def _generate_personalized_content(self, concept, style):
        """生成个性化教学内容"""
        
        # 根据不同风格定制prompt
        if style == "practical":
            instruction = """你是一个实践导向的AI导师。请用简洁的语言解释概念,重点是:
1. 用生活化的比喻快速说明
2. 给出简单的代码示例
3. 鼓励动手尝试
回复要简短直接,不超过150字。"""
        
        elif style == "theoretical":
            instruction = """你是一个理论导向的AI导师。请深入解释概念,重点是:
1. 准确的定义和术语
2. 背后的原理和理论基础
3. 相关的数学表达(如果有)
回复要详细完整,可以300字左右。"""
        
        else:  # balanced
            instruction = """你是一个平衡型AI导师。请全面解释概念,重点是:
1. 清晰的概念说明
2. 简单的例子辅助理解
3. 理论和实践结合
回复要适中,200字左右。"""
        
        # 调用DeepSeek LLM生成内容
        response = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": f"请解释: {concept}"}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def record_behavior(self, student_id, behavior_data):
        """记录学生行为,用于隐式偏好学习"""
        profile = self.profiles.get(student_id)
        
        if not profile:
            return
        
        # 更新行为数据
        profile.update_from_implicit(behavior_data)
        
        print(f"📊 行为已记录: {behavior_data}")
        print(f"📈 当前推断: 学习类型={profile.learning_style['type']}")
    
    def get_student_profile(self, student_id):
        """获取学生画像"""
        profile = self.profiles.get(student_id)
        if profile:
            return profile.get_summary()
        return None
    
    def _save_preference(self, student_id, preference_text):
        """保存偏好到记忆系统"""
        self.memory.add(
            messages=[{"role": "system", "content": preference_text}],
            user_id=student_id,
            metadata={"type": "preference", "timestamp": datetime.now().isoformat()}
        )
    
    def _save_interaction(self, student_id, interaction_text):
        """保存交互记录"""
        self.memory.add(
            messages=[{"role": "system", "content": interaction_text}],
            user_id=student_id,
            metadata={"type": "interaction", "timestamp": datetime.now().isoformat()}
        )


class PersonalizationEvaluator:
    """个性化效果评估器"""
    
    def __init__(self):
        self.results = {
            "control_group": [],  # 对照组(无个性化)
            "experiment_group": []  # 实验组(有个性化)
        }
    
    def record_result(self, group, completion_rate, satisfaction, learning_days):
        """记录测试结果"""
        self.results[group].append({
            "completion_rate": completion_rate,
            "satisfaction": satisfaction,
            "learning_days": learning_days
        })
    
    def analyze_results(self):
        """分析A/B测试结果"""
        print("\n" + "="*50)
        print("个性化效果评估 (A/B测试结果)")
        print("="*50)
        
        # 对照组统计
        control = self.results["control_group"]
        if control:
            avg_completion_c = sum(r["completion_rate"] for r in control) / len(control)
            avg_satisfaction_c = sum(r["satisfaction"] for r in control) / len(control)
            avg_days_c = sum(r["learning_days"] for r in control) / len(control)
            
            print("\n【对照组 - 通用教学】")
            print(f"  完成率: {avg_completion_c:.1f}%")
            print(f"  满意度: {avg_satisfaction_c:.1f}/5")
            print(f"  学习时长: {avg_days_c:.1f}天")
        
        # 实验组统计
        experiment = self.results["experiment_group"]
        if experiment:
            avg_completion_e = sum(r["completion_rate"] for r in experiment) / len(experiment)
            avg_satisfaction_e = sum(r["satisfaction"] for r in experiment) / len(experiment)
            avg_days_e = sum(r["learning_days"] for r in experiment) / len(experiment)
            
            print("\n【实验组 - 个性化教学】")
            print(f"  完成率: {avg_completion_e:.1f}%")
            print(f"  满意度: {avg_satisfaction_e:.1f}/5")
            print(f"  学习时长: {avg_days_e:.1f}天")
            
            # 计算提升
            if control:
                completion_improvement = ((avg_completion_e - avg_completion_c) / avg_completion_c) * 100
                satisfaction_improvement = ((avg_satisfaction_e - avg_satisfaction_c) / avg_satisfaction_c) * 100
                days_improvement = ((avg_days_c - avg_days_e) / avg_days_c) * 100
                
                print("\n【个性化提升效果】")
                print(f"  完成率提升: {completion_improvement:+.1f}%")
                print(f"  满意度提升: {satisfaction_improvement:+.1f}%")
                print(f"  时间缩短: {days_improvement:+.1f}%")
                print("\n✅ 个性化显著提升了学习效果!")


# ==================== 使用示例 ====================

def demo_personalized_teaching():
    """演示个性化教学"""
    
    print("\n" + "="*60)
    print("个性化AI学习助手 - 实战演示")
    print("="*60)
    
    # 创建助手
    assistant = PersonalizedTeachingAssistant()
    
    # === 场景1: 实践型学生 ===
    print("\n【场景1: 实践型学生Alice】")
    
    # 模拟用户输入(实际使用时会真实输入)
    print("\n=== 欢迎新学生: alice_001 ===\n")
    print("为了提供更好的学习体验,请回答几个问题:\n")
    print("1. 你更喜欢哪种学习方式?")
    print("   A. 快速上手,边做边学(实践型)")
    print("   选择: A")
    
    # 直接创建实践型学生画像
    alice_profile = StudentProfile("alice_001")
    alice_profile.learning_style["type"] = "practical"
    alice_profile.learning_style["pace"] = "fast"
    assistant.profiles["alice_001"] = alice_profile
    assistant._save_preference("alice_001", "学习风格: practical")
    
    print(f"\n✅ 画像已创建! 学习风格: practical, 节奏: fast\n")
    
    # 教授概念(实践型)
    assistant.teach_concept("alice_001", "什么是注意力机制")
    
    # 模拟行为: Alice跳过理论,直接看代码
    print("\n[Alice的行为: 跳过理论说明,直接查看代码示例]")
    assistant.record_behavior("alice_001", {
        "skip_theory_count": 3,
        "code_view_time": 300,  # 秒
        "question_frequency": 5
    })
    
    # === 场景2: 理论型学生 ===
    print("\n\n【场景2: 理论型学生Bob】")
    
    print("\n=== 欢迎新学生: bob_002 ===\n")
    print("为了提供更好的学习体验,请回答几个问题:\n")
    print("1. 你更喜欢哪种学习方式?")
    print("   B. 系统学习,理解原理(理论型)")
    print("   选择: B")
    
    # 创建理论型学生画像
    bob_profile = StudentProfile("bob_002")
    bob_profile.learning_style["type"] = "theoretical"
    bob_profile.learning_style["pace"] = "moderate"
    assistant.profiles["bob_002"] = bob_profile
    assistant._save_preference("bob_002", "学习风格: theoretical")
    
    print(f"\n✅ 画像已创建! 学习风格: theoretical, 节奏: moderate\n")
    
    # 教授相同概念(理论型)
    assistant.teach_concept("bob_002", "什么是注意力机制")
    
    # 模拟行为: Bob仔细阅读理论
    print("\n[Bob的行为: 仔细阅读理论,较少跳过]")
    assistant.record_behavior("bob_002", {
        "skip_theory_count": 0,
        "theory_view_time": 600,  # 秒
        "question_frequency": 2
    })
    
    # === 查看画像 ===
    print("\n\n" + "="*60)
    print("学生画像总结")
    print("="*60)
    
    alice_summary = assistant.get_student_profile("alice_001")
    bob_summary = assistant.get_student_profile("bob_002")
    
    print(f"\nAlice的画像: {alice_summary}")
    print(f"Bob的画像: {bob_summary}")
    
    # === 效果评估 ===
    print("\n\n" + "="*60)
    print("模拟A/B测试效果")
    print("="*60)
    
    evaluator = PersonalizationEvaluator()
    
    # 对照组(无个性化)数据
    evaluator.record_result("control_group", 65, 3.2, 15)
    evaluator.record_result("control_group", 60, 3.0, 16)
    evaluator.record_result("control_group", 70, 3.5, 14)
    
    # 实验组(有个性化)数据
    evaluator.record_result("experiment_group", 85, 4.3, 11)
    evaluator.record_result("experiment_group", 88, 4.5, 10)
    evaluator.record_result("experiment_group", 82, 4.0, 12)
    
    # 分析结果
    evaluator.analyze_results()
    
    print("\n" + "="*60)
    print("演示完成!")
    print("="*60)


def interactive_demo():
    """交互式演示(可选)"""
    
    print("\n" + "="*60)
    print("个性化AI学习助手 - 交互式体验")
    print("="*60)
    
    assistant = PersonalizedTeachingAssistant()
    
    # 输入学生ID
    student_id = input("\n请输入你的学生ID: ").strip()
    
    # 初始化学生(会收集显式偏好)
    assistant.initialize_student(student_id)
    
    # 选择要学习的概念
    print("\n请选择要学习的概念:")
    print("1. 注意力机制")
    print("2. Transformer架构")
    print("3. 反向传播算法")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    concepts = {
        "1": "注意力机制",
        "2": "Transformer架构",
        "3": "反向传播算法"
    }
    
    concept = concepts.get(choice, "注意力机制")
    
    # 教授概念
    assistant.teach_concept(student_id, concept)
    
    # 查看画像
    profile = assistant.get_student_profile(student_id)
    print(f"\n📋 你的学习画像: {profile}")
    
    print("\n感谢使用个性化AI学习助手!")


if __name__ == "__main__":
    # 检查API配置
    if not DEEPSEEK_API_KEY:
        print("❌ 错误: 请在.env文件中配置DEEPSEEK_API_KEY")
        print("示例配置:")
        print("DEEPSEEK_API_KEY=your_api_key_here")
        print("OPENAI_BASE_URL=https://api.deepseek.com")
        exit(1)
    
    print(f"✅ DeepSeek API配置成功")
    print(f"   模型: {DEEPSEEK_MODEL}")
    print(f"   Base URL: {DEEPSEEK_BASE_URL}")
    
    # 运行自动演示
    demo_personalized_teaching()
    
    # 如果想体验交互式版本,取消下面的注释
    # print("\n\n")
    # interactive_demo()
