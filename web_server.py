"""
============================================================
🌐 具身智能多 Agent 协作报告 — Web UI 后端
============================================================
基于 Flask 的 Web 服务，通过 SSE（Server-Sent Events）
将三个 Agent 的实时输出流式推送到前端。

作者: 20230420刘禹哲
日期: 2026-05-14
============================================================
"""

import json
import os
import sys
import time
from datetime import datetime

# 修复 Windows 终端 GBK 编码无法输出 Unicode 的问题
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from flask import Flask, Response, jsonify, request, send_from_directory
from openai import OpenAI

app = Flask(__name__, static_folder=".", static_url_path="")

# ============================================================
# 🧠 Agent System Prompts（与 embodied_ai_hw.py 保持一致）
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
# 📡 API 调用（支持流式输出）
# ============================================================

def chat_with_agent_stream(api_key, base_url, model, system_prompt, user_content):
    """
    流式调用大模型 API，逐 token 返回生成器。

    参数:
        api_key      (str): API 密钥
        base_url     (str): API 基础地址
        model        (str): 模型名称
        system_prompt(str): 系统提示词
        user_content (str): 用户输入内容

    Yields:
        str: 每次生成的文本片段（delta）
    """
    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        max_tokens=4096,
        top_p=0.9,
        stream=True,  # 开启流式输出
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


# ============================================================
# 🌐 路由定义
# ============================================================

@app.route("/")
def index():
    """提供前端页面"""
    return send_from_directory(".", "index.html")


@app.route("/api/run", methods=["POST"])
def run_agents():
    """
    接收前端配置并启动三 Agent 串行工作流。
    使用 SSE 实时推送每个 Agent 的输出。
    """
    data = request.json
    api_key = data.get("api_key", "").strip()
    base_url = data.get("base_url", "").strip()
    model = data.get("model", "mimo-v2.5-pro").strip()

    if not api_key:
        return jsonify({"error": "请填写 API Key"}), 400
    if not base_url:
        return jsonify({"error": "请填写 Base URL"}), 400

    def generate_sse():
        """SSE 事件流生成器"""
        outputs = {}

        # ---------- Agent 1: PM Agent ----------
        yield _sse_event("agent_start", {
            "agent": 1,
            "name": "PM Agent",
            "task": "分析具身智能核心物理矛盾"
        })

        agent1_input = (
            "请分析具身智能（Embodied AI）在实际部署中面临的核心物理矛盾："
            "即高算力需求（大模型推理、实时感知、运动控制）与机器人硬件的低功耗、"
            "小体积约束之间的根本冲突。请给出详细的分析报告。"
        )

        try:
            agent1_output = ""
            for token in chat_with_agent_stream(api_key, base_url, model,
                                                 AGENT_1_SYSTEM, agent1_input):
                agent1_output += token
                yield _sse_event("token", {"agent": 1, "content": token})

            outputs["agent1"] = agent1_output
            yield _sse_event("agent_done", {"agent": 1})

        except Exception as e:
            yield _sse_event("error", {
                "agent": 1,
                "message": f"Agent 1 调用失败: {str(e)}"
            })
            return

        # ---------- Agent 2: Architecture Agent ----------
        yield _sse_event("agent_start", {
            "agent": 2,
            "name": "Architecture Agent",
            "task": "设计云-边-端协同算力架构"
        })

        agent2_input = (
            f"以下是 PM Agent 对具身智能算力痛点的分析报告：\n\n"
            f"---\n{agent1_output}\n---\n\n"
            f"请基于以上分析，提出一套完整的 '云-边-端协同（大小脑分离）' 算力分配架构方案。"
        )

        try:
            agent2_output = ""
            for token in chat_with_agent_stream(api_key, base_url, model,
                                                 AGENT_2_SYSTEM, agent2_input):
                agent2_output += token
                yield _sse_event("token", {"agent": 2, "content": token})

            outputs["agent2"] = agent2_output
            yield _sse_event("agent_done", {"agent": 2})

        except Exception as e:
            yield _sse_event("error", {
                "agent": 2,
                "message": f"Agent 2 调用失败: {str(e)}"
            })
            return

        # ---------- Agent 3: Algorithm Agent ----------
        yield _sse_event("agent_start", {
            "agent": 3,
            "name": "Algorithm Agent",
            "task": "端侧模型轻量化与算力优化"
        })

        agent3_input = (
            f"以下是 Architecture Agent 提出的云-边-端协同架构方案：\n\n"
            f"---\n{agent2_output}\n---\n\n"
            f"请针对该架构中端侧（小脑）算力不足的问题，"
            f"提出一整套具体的模型轻量化与算力优化落地手段。"
        )

        try:
            agent3_output = ""
            for token in chat_with_agent_stream(api_key, base_url, model,
                                                 AGENT_3_SYSTEM, agent3_input):
                agent3_output += token
                yield _sse_event("token", {"agent": 3, "content": token})

            outputs["agent3"] = agent3_output
            yield _sse_event("agent_done", {"agent": 3})

        except Exception as e:
            yield _sse_event("error", {
                "agent": 3,
                "message": f"Agent 3 调用失败: {str(e)}"
            })
            return

        # ---------- 生成报告并保存 ----------
        report = _generate_report(
            outputs["agent1"], outputs["agent2"], outputs["agent3"], model
        )

        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Project1_Solution.md"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        yield _sse_event("complete", {
            "file_path": output_path,
            "char_count": len(report),
            "report": report,
        })

    return Response(
        generate_sse(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# 🔧 辅助函数
# ============================================================

def _sse_event(event_type: str, data: dict) -> str:
    """格式化 SSE 事件"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _generate_report(a1: str, a2: str, a3: str, model: str) -> str:
    """生成 Markdown 报告"""
    return f"""# 具身智能算力瓶颈解决方案

> 📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 🤖 生成方式: 多 Agent 协作（PM → Architecture → Algorithm）
> 🧠 使用模型: {model}

---

## 第一部分：核心矛盾分析（PM Agent）

{a1}

---

## 第二部分：云-边-端协同架构设计（Architecture Agent）

{a2}

---

## 第三部分：端侧模型轻量化与算力优化（Algorithm Agent）

{a3}

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


# ============================================================
# 🚀 启动
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🌐 Web UI 已启动")
    print("   访问地址: http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
