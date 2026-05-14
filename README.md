# 🤖 具身智能算力瓶颈解决方案 — 多 Agent 协作平台
**超大规模数字集成电路设计 (VLSI Digital IC Design) — Project 1**

![WebUI Screenshot](https://img.shields.io/badge/UI-VibeCoding_Premium-00E5FF?style=for-the-badge)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Online_Access-success?style=for-the-badge)](https://lpiuma.github.io/VLSI-Digital-IC-Design/)
![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask)

本项目是针对具身智能（Embodied AI）在边缘端侧部署时面临的“高算力需求 vs 低功耗硬件约束”核心矛盾，构建的**多 Agent 自动接力生成与系统架构设计平台**。

通过模拟 **PM (产品经理) → Architecture (系统架构师) → Algorithm (算法专家)** 三个角色的串行推理与协作，自动产出深度定制的软硬件协同架构与模型轻量化落地报告。

---

## 🌟 核心特性与架构设计

本项目提供两种交互形态：**命令行流式工具** 与 **Web 可视化工作台**。

### 1. 三级串行 Agent 推理链路
*   **📊 Agent 1 (PM Agent)**：剖析端侧算力痛点，量化感知、规划与控制模块的计算开销与功耗限制。
*   **🏗️ Agent 2 (Architecture Agent)**：基于痛点提出“大小脑分离”的云-边-端协同分层算力调度与卸载方案。
*   **⚡ Agent 3 (Algorithm Agent)**：针对小脑端侧硬件，设计具体的知识蒸馏、INT4 量化与异构计算加速策略。

### 2. WebUI 交互体验
*   **纯前端 API 直连模式**：支持直接在静态页面直连跨域大模型 API，自动拉取可用模型列表与快捷预填。
*   **SSE 实时流式渲染**：后端基于 Flask 建立 Server-Sent Events 流，逐 Token 将三个 Agent 的思考过程无缝推送到前端进行 Markdown 实时渲染。
*   **一键交付**：运行完毕自动拼接汇总并提供 `.md` 原件导出。

---

## 🚀 快速启动

### 🌐 极速体验（在线版）
无需配置本地环境，直接访问托管在 GitHub Pages 的直连平台：
👉 **[点击进入多 Agent 协作工作台 (线上版)](https://lpiuma.github.io/VLSI-Digital-IC-Design/)**

> **提示**：线上版支持直接填入你的 API Key，点击快捷提供商（如 DeepSeek、MiMo、OpenRouter等）自动拉取模型列表。

---

### 💻 本地部署

#### 准备工作
确保已安装 Python 环境与必要的依赖库：
```bash
pip install openai flask
```

配置大模型 API 密钥（推荐配置在环境变量中，也可在 Web 界面直接输入）：
*   **Windows CMD**: `set MIMO_API_KEY=sk-xxxxxx`
*   **Windows PowerShell**: `$env:MIMO_API_KEY="sk-xxxxxx"`
*   **Linux/macOS**: `export MIMO_API_KEY="sk-xxxxxx"`

#### 模式一：终端版
在终端中输出带有进度提示的生成报告，并自动保存到本地：
```bash
python embodied_ai_hw.py
```

#### 模式二：WebUI 版（本地服务）
启动本地 Flask 引擎，在浏览器中进行全流程配置与实时可视化流监控：
```bash
python web_server.py
```
启动后访问：[http://localhost:5000](http://localhost:5000)

---

## 📁 目录结构说明

```text
.
├── embodied_ai_hw.py       # 终端核心逻辑与 Agent Prompt 定义
├── web_server.py           # Flask 后端流式推送服务
├── index.html              # 沉浸式前端可视化交互界面
├── Project1_Solution.md    # 最终汇总生成的 Markdown 作业报告（示例输出）
└── README.md               # 项目文档说明
```
