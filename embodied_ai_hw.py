"""
============================================================
🤖 具身智能算力瓶颈解决方案 — 多 Agent 协作自动报告生成
============================================================
本脚本通过三个串行 Agent（PM → Architecture → Algorithm）
接力调用大模型 API，自动生成一份关于"具身智能算力瓶颈解决方案"
的完整作业报告，并保存为 Markdown 文件。

作者: 20230420刘禹哲
日期: 2026-05-13
============================================================
"""

import os
import sys
from datetime import datetime

from openai import OpenAI


# ============================================================
# 🔧 配置区 — 请根据实际情况修改以下参数
# ============================================================

# --- API Key ---
# 从环境变量 MIMO_API_KEY 中读取，请确保已设置：
#   Windows CMD:   set MIMO_API_KEY=sk-xxxxxxx
#   Windows PS:    $env:MIMO_API_KEY="sk-xxxxxxx"
#   Linux/macOS:   export MIMO_API_KEY=sk-xxxxxxx
API_KEY = os.getenv("MIMO_API_KEY")

# --- Base URL ---
# ⚠️ 请根据你使用的 API 提供商修改此 URL：
#   - 小米 MiMo 官方：   https://api.mimo.xiaomi.com/v1
#   - OpenRouter:        https://openrouter.ai/api/v1
#   - 其他兼容 OpenAI 格式的服务商：填入对应地址
BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"  # ← 修改此处

# --- 模型名称 ---
# ⚠️ 可选模型：mimo-v2-pro (推理更强) / mimo-v2-flash (速度更快)
MODEL_NAME = "mimo-v2.5-pro"  # ← 修改此处

# --- 输出文件路径 ---
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Project1_Solution.md")


# ============================================================
# 🧠 Agent System Prompts（系统提示词）
# ============================================================

AGENT_1_SYSTEM = """你是一位资深的具身智能产品经理（PM Agent）。
你的任务是深入分析具身智能（Embodied AI）在实际部署中所面临的 **核心物理矛盾**：
即 "高算力需求" 与 "机器人低功耗、小体积硬件约束" 之间的根本冲突。

请从以下维度展开分析：
1. **算力需求侧**：大模型推理（LLM/VLM）、实时感知（3D 视觉、点云处理）、运动控制（MPC/RL）各自的算力量级。
2. **硬件约束侧**：机器人端侧（如人形机器人、无人机、AMR）的功耗预算（通常 10-50W）、散热限制、体积/重量限制。
3. **矛盾的本质**：为什么不能简单地 "装一块更强的芯片" 来解决问题？从功耗墙、散热墙、成本约束、实时性要求等角度阐述。
4. **问题的紧迫性**：结合 2025-2026 年产业趋势（如人形机器人爆发、大模型端侧化），说明为什么现在必须解决这个矛盾。

输出格式要求：
- 使用 Markdown 格式
- 层次清晰，包含小标题
- 要有具体的数据和案例支撑（如 Jetson Orin 的算力/功耗比、GPT-4 级别模型的推理算力需求等）
- 篇幅控制在 800-1200 字"""

AGENT_2_SYSTEM = """你是一位具身智能系统架构师（Architecture Agent）。
你将接收来自 PM Agent 的具身智能算力痛点分析报告，基于此提出一套完整的 **"云-边-端协同"算力分配架构**（也称为"大小脑分离架构"）。

请按以下框架展开方案设计：
1. **架构总览**：画出（用文字描述）云-边-端三级算力分配的逻辑架构图，明确每层的职责。
2. **大脑（Cloud/Edge）层**：
   - 承载哪些高算力任务？（如 LLM 推理、全局路径规划、离线训练等）
   - 需要什么级别的硬件？（如 A100 集群、边缘服务器等）
   - 通信延迟如何保证？（5G/WiFi 6 方案）
3. **小脑（End-device）层**：
   - 端侧芯片选型建议（如 Jetson Orin NX、RK3588、地平线 J5 等）
   - 必须本地处理的实时任务（如避障、力控、紧急制动等）
   - 端侧算力预算分配（各任务占比）
4. **云边端协同机制**：
   - 任务动态卸载（Task Offloading）策略
   - 模型分层部署（哪些模型层放云端，哪些放端侧）
   - 网络中断时的降级方案（Fallback）
5. **该架构相比纯端侧/纯云端方案的优势对比**

输出格式要求：
- 使用 Markdown 格式
- 包含架构层级的表格对比
- 提供具体的硬件选型和参数
- 篇幅控制在 1000-1500 字"""

AGENT_3_SYSTEM = """你是一位端侧 AI 算法优化专家（Algorithm Agent）。
你将接收来自 Architecture Agent 的云-边-端协同架构方案，针对其中 **端侧（小脑）算力不足** 的问题，
提出一整套具体的 **模型轻量化与算力优化落地手段**。

请从以下技术路径展开：
1. **模型压缩与轻量化**：
   - 知识蒸馏（Knowledge Distillation）：教师-学生模型的具体设计
   - 模型剪枝（Pruning）：结构化剪枝 vs 非结构化剪枝的选择
   - 低秩分解（Low-Rank Factorization）
2. **量化部署**：
   - INT8 / INT4 / 混合精度量化方案
   - 量化感知训练（QAT） vs 训练后量化（PTQ）的取舍
   - 具体的量化工具链推荐（TensorRT, ONNX Runtime, MLC-LLM 等）
3. **异构计算优化**：
   - CPU + GPU + NPU + DSP 的任务分配策略
   - 算子级别的硬件亲和性优化
   - 流水线并行（Pipeline Parallelism）在端侧的应用
4. **端侧专用模型设计**：
   - 轻量化网络架构（MobileNet, EfficientNet, TinyLLM 等）
   - 针对机器人任务的定制化模型裁剪
5. **实际落地案例**：
   - 给出 1-2 个具体的端侧部署案例（如在 Jetson Orin 上部署 7B 参数模型）
   - 包含优化前后的延迟/吞吐量/功耗对比数据

输出格式要求：
- 使用 Markdown 格式
- 包含技术对比表格
- 有具体的数据支撑
- 篇幅控制在 1000-1500 字"""


# ============================================================
# 📡 通用 API 调用函数
# ============================================================

def chat_with_agent(system_prompt: str, user_content: str) -> str:
    """
    封装 OpenAI 兼容格式的大模型 API 调用。

    参数:
        system_prompt (str): Agent 的系统级提示词，定义其角色与任务
        user_content  (str): 用户/上游 Agent 传递的具体内容

    返回:
        str: 模型生成的回复文本
    """
    # 初始化客户端（每次调用都新建，避免连接池问题）
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,       # 适中的创造性
            max_tokens=4096,       # 最大输出长度
            top_p=0.9,
        )
        # 提取助手回复内容
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"\n❌ API 调用失败: {e}")
        print("💡 请检查：")
        print("   1. 环境变量 MIMO_API_KEY 是否已设置")
        print("   2. BASE_URL 是否正确")
        print("   3. MODEL_NAME 是否在该平台可用")
        print(f"   当前配置: BASE_URL={BASE_URL}, MODEL={MODEL_NAME}")
        sys.exit(1)


# ============================================================
# 🖨️ 终端美化输出函数
# ============================================================

def print_header():
    """打印脚本启动的头部信息"""
    print("\n" + "=" * 60)
    print("🤖 具身智能算力瓶颈解决方案 — 多 Agent 协作报告生成器")
    print("=" * 60)
    print(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API 地址: {BASE_URL}")
    print(f"🧠 调用模型: {MODEL_NAME}")
    print("=" * 60)


def print_agent_start(agent_name: str, agent_emoji: str, description: str):
    """打印某个 Agent 开始工作的提示"""
    print(f"\n{'─' * 60}")
    print(f"{agent_emoji} [{agent_name}] 正在思考中...")
    print(f"   📋 任务: {description}")
    print(f"{'─' * 60}")


def print_agent_result(agent_name: str, agent_emoji: str, result: str):
    """打印某个 Agent 的输出结果"""
    print(f"\n{'━' * 60}")
    print(f"✅ [{agent_name}] 输出完成 {agent_emoji}")
    print(f"{'━' * 60}")
    # 输出前 500 字符作为预览（避免终端刷屏）
    preview = result[:500] + "\n... (已截断，完整内容将写入 Markdown 文件)" if len(result) > 500 else result
    print(preview)
    print(f"{'━' * 60}")


# ============================================================
# 📝 Markdown 报告生成函数
# ============================================================

def generate_report(agent1_output: str, agent2_output: str, agent3_output: str) -> str:
    """
    将三个 Agent 的输出汇总为一份完整的 Markdown 报告。

    参数:
        agent1_output: PM Agent 的痛点分析输出
        agent2_output: Architecture Agent 的架构方案输出
        agent3_output: Algorithm Agent 的优化方案输出

    返回:
        str: 完整的 Markdown 报告内容
    """
    report = f"""# 具身智能算力瓶颈解决方案

> 📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 🤖 生成方式: 多 Agent 协作（PM → Architecture → Algorithm）
> 🧠 使用模型: {MODEL_NAME}

---

## 第一部分：核心矛盾分析（PM Agent）

{agent1_output}

---

## 第二部分：云-边-端协同架构设计（Architecture Agent）

{agent2_output}

---

## 第三部分：端侧模型轻量化与算力优化（Algorithm Agent）

{agent3_output}

---

## 总结

本报告由三个专业 Agent 协作完成：
1. **PM Agent** 识别了具身智能中"高算力需求"与"低功耗硬件约束"的核心物理矛盾
2. **Architecture Agent** 提出了"云-边-端协同（大小脑分离）"的系统架构方案
3. **Algorithm Agent** 给出了端侧模型轻量化的具体技术路径和落地方案

三者形成了从 **问题定义 → 架构设计 → 算法落地** 的完整解决链路。

---

*本报告由 AI 多 Agent 系统自动生成，仅供学术参考。*
"""
    return report


# ============================================================
# 🚀 主执行流程
# ============================================================

def main():
    """主函数：串行执行三个 Agent 的工作流"""

    # --- 0. 前置检查 ---
    if not API_KEY:
        print("\n❌ 错误: 未检测到环境变量 MIMO_API_KEY！")
        print("💡 请先设置 API Key：")
        print('   Windows PowerShell: $env:MIMO_API_KEY="你的API密钥"')
        print('   Windows CMD:        set MIMO_API_KEY=你的API密钥')
        print('   Linux/macOS:        export MIMO_API_KEY="你的API密钥"')
        sys.exit(1)

    # --- 1. 打印头部 ---
    print_header()

    # === Agent 1: PM Agent ===
    print_agent_start(
        "Agent 1 — PM Agent", "📊",
        "分析具身智能的算力核心矛盾"
    )
    agent1_input = (
        "请分析具身智能（Embodied AI）在实际部署中面临的核心物理矛盾："
        "即高算力需求（大模型推理、实时感知、运动控制）与机器人硬件的低功耗、"
        "小体积约束之间的根本冲突。请给出详细的分析报告。"
    )
    agent1_output = chat_with_agent(AGENT_1_SYSTEM, agent1_input)
    print_agent_result("Agent 1 — PM Agent", "📊", agent1_output)

    # === Agent 2: Architecture Agent ===
    print_agent_start(
        "Agent 2 — Architecture Agent", "🏗️",
        "设计云-边-端协同算力架构"
    )
    agent2_input = (
        f"以下是 PM Agent 对具身智能算力痛点的分析报告：\n\n"
        f"---\n{agent1_output}\n---\n\n"
        f"请基于以上分析，提出一套完整的 '云-边-端协同（大小脑分离）' 算力分配架构方案。"
    )
    agent2_output = chat_with_agent(AGENT_2_SYSTEM, agent2_input)
    print_agent_result("Agent 2 — Architecture Agent", "🏗️", agent2_output)

    # === Agent 3: Algorithm Agent ===
    print_agent_start(
        "Agent 3 — Algorithm Agent", "⚡",
        "端侧模型轻量化与算力优化"
    )
    agent3_input = (
        f"以下是 Architecture Agent 提出的云-边-端协同架构方案：\n\n"
        f"---\n{agent2_output}\n---\n\n"
        f"请针对该架构中端侧（小脑）算力不足的问题，"
        f"提出一整套具体的模型轻量化与算力优化落地手段。"
    )
    agent3_output = chat_with_agent(AGENT_3_SYSTEM, agent3_input)
    print_agent_result("Agent 3 — Algorithm Agent", "⚡", agent3_output)

    # === 汇总输出 ===
    print(f"\n{'=' * 60}")
    print("📄 正在生成最终 Markdown 报告...")
    print(f"{'=' * 60}")

    report_content = generate_report(agent1_output, agent2_output, agent3_output)

    # 写入文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n✅ 报告已成功保存到: {OUTPUT_FILE}")
    print(f"📏 报告总字数: {len(report_content)} 字符")
    print(f"\n{'=' * 60}")
    print("🎉 全部 Agent 任务完成！")
    print(f"{'=' * 60}\n")


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    main()
