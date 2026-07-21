#!/usr/bin/env python3
"""批量写入今日日报 10 个项目的评估结果"""
import json, sys
sys.path.insert(0, r'E:\AI\football')
from evaluator import save_db
from datetime import datetime

evaluations = [
    {
        "url": "https://github.com/ollama/ollama",
        "name": "ollama",
        "description": "本地 LLM 运行引擎，支持几乎所有开源模型，176K stars，Go 编写，MIT 协议",
        "category": "AI/ML", "subcategory": "本地推理",
        "language": "Go", "stars": 176000, "last_commit_days": 14,
        "has_readme": True, "has_dockerfile": True, "has_demo": True,
        "requires_gpu": False, "requires_node": False,
        "dependency_complexity": "moderate",
        "code_quality": 5, "doc_quality": 5, "match_score": 3.5,
        "overall_score": 3.8, "verdict": "worth_testing",
        "reason": "顶级项目；Windows 原生支持；用户已用 DeepSeek 云端模型，本地 LLM 互补而非替代；公司网络可能限制模型下载",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["LLM", "本地推理", "Go", "MIT"]
    },
    {
        "url": "https://github.com/continuedev/continue",
        "name": "Continue",
        "description": "开源 AI 编程助手（VS Code/JetBrains/CLI），34K stars，2026年已进入只读状态（v2.0.0 最终版），Apache 2.0",
        "category": "开发工具", "subcategory": "AI编程助手",
        "language": "TypeScript", "stars": 34000, "last_commit_days": 90,
        "has_readme": True, "has_dockerfile": False, "has_demo": False,
        "requires_gpu": False, "requires_node": True,
        "dependency_complexity": "moderate",
        "code_quality": 5, "doc_quality": 5, "match_score": 1.5,
        "overall_score": 2.0, "verdict": "reference_only",
        "reason": "已停止维护（只读）；功能与 Claude Code 重叠，无增量价值；架构参考：MCP 集成、Rules 系统、多模型路由设计值得学习",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["IDE", "AI编程", "架构参考", "只读"]
    },
    {
        "url": "https://github.com/gangtao/AgentPitch",
        "name": "AgentPitch",
        "description": "LLM 驱动的足球模拟——每个球员都是 AI Agent。Python/JS/Rust 三语言支持，FIFA 2026 实时模拟，252 commits，Apache 2.0",
        "category": "足球分析", "subcategory": "AI足球模拟",
        "language": "Python", "stars": 200, "last_commit_days": 9,
        "has_readme": True, "has_dockerfile": False, "has_demo": True,
        "requires_gpu": False, "requires_node": False,
        "dependency_complexity": "moderate",
        "code_quality": 4, "doc_quality": 4, "match_score": 4.5,
        "overall_score": 4.2, "verdict": "install_now",
        "reason": "高度匹配用户兴趣；活跃开发中（9天前更新）；设计精巧——LLM 生成策略代码到沙箱执行到赛后进化；MCP 集成潜力大；不依赖 GPU",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["LLM", "足球模拟", "AI Agent", "FIFA2026", "开源"]
    },
    {
        "url": "https://github.com/jonaidshianifar/ai-world-cup",
        "name": "ai-world-cup",
        "description": "LLM 世界杯预测基准——用标准化 prompt 测试各 LLM 的预测能力，手动提交+自动评分+排行榜，MIT",
        "category": "足球分析", "subcategory": "预测基准",
        "language": "Python", "stars": 30, "last_commit_days": 30,
        "has_readme": True, "has_demo": True, "has_dockerfile": False,
        "requires_gpu": False, "requires_node": False,
        "dependency_complexity": "simple",
        "code_quality": 3, "doc_quality": 4, "match_score": 3.0,
        "overall_score": 3.2, "verdict": "worth_testing",
        "reason": "轻量级、易上手；基准测试思路可借鉴（标准化 prompt到评分到排行榜）；用户无法直接参与（需等比赛结果验证）；可作为预测系统的评分参考设计",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["LLM", "预测", "基准测试", "世界杯"]
    },
    {
        "url": "https://github.com/MouroshK/World_cup_2026_prediction",
        "name": "World_cup_2026_prediction",
        "description": "端到端数据工程+ML 预测 2026 世界杯。LightGBM 模型、Streamlit 仪表板、交叉验证、蒙特卡洛模拟",
        "category": "足球分析", "subcategory": "ML预测",
        "language": "Python", "stars": 50, "last_commit_days": 20,
        "has_readme": True, "has_demo": True, "has_dockerfile": False,
        "requires_gpu": False, "requires_node": False,
        "dependency_complexity": "moderate",
        "code_quality": 4, "doc_quality": 3, "match_score": 4.0,
        "overall_score": 3.8, "verdict": "worth_testing",
        "reason": "真正的 ML pipeline（LightGBM + 特征工程 + 交叉验证），非硬编码规则；Streamlit 在线演示可直接看效果；数据管道设计可复用；依赖中等",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["ML", "LightGBM", "Streamlit", "世界杯", "数据管道"]
    },
    {
        "url": "https://github.com/abhinav-phi/sports_cv",
        "name": "sports_cv",
        "description": "YOLOv8 体育 CV 分析套件——足球+板球。自动标注视频：球员追踪、传球检测、xG、热力图、阵型识别",
        "category": "足球分析", "subcategory": "计算机视觉",
        "language": "Python", "stars": 30, "last_commit_days": 30,
        "has_readme": True, "has_demo": True, "has_dockerfile": False,
        "requires_gpu": True, "requires_node": False,
        "dependency_complexity": "complex",
        "code_quality": 4, "doc_quality": 4, "match_score": 2.5,
        "overall_score": 2.0, "verdict": "reference_only",
        "reason": "需要 GPU（YOLOv8+CUDA）用户没有；架构优雅（homography/kalman/team_classifier 模块化清晰）；代码设计可参考；未来有 GPU 后可安装",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["CV", "YOLOv8", "球员追踪", "需要GPU", "架构参考"]
    },
    {
        "url": "https://github.com/DevaNandanJS/Football-Tactical-Analysis-AI-Coaching",
        "name": "Football-Tactical-Analysis-AI-Coaching",
        "description": "足球战术 AI 教练系统——YOLO+BoTSORT 追踪，自动生成热力图、传球网络、战术仪表板",
        "category": "足球分析", "subcategory": "战术分析",
        "language": "Python", "stars": 20, "last_commit_days": 60,
        "has_readme": True, "has_demo": True, "has_dockerfile": False,
        "requires_gpu": True, "requires_node": False,
        "dependency_complexity": "complex",
        "code_quality": 3, "doc_quality": 3, "match_score": 2.0,
        "overall_score": 1.5, "verdict": "skip",
        "reason": "需要 GPU；与 sports_cv 功能重叠但文档和代码质量不如后者；开发者用 Gemini 辅助开发；不如先参考 sports_cv 的架构",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["CV", "战术分析", "需要GPU", "YOLO"]
    },
    {
        "url": "https://github.com/gaemi/agentic-fc",
        "name": "agentic-fc",
        "description": "AI Agent 驱动的足球经理模拟——通过 MCP 协议控制，TUI 终端观看。Go 编写，FM 风格属性系统",
        "category": "足球分析", "subcategory": "足球经理模拟",
        "language": "Go", "stars": 50, "last_commit_days": 12,
        "has_readme": True, "has_demo": True, "has_dockerfile": False,
        "requires_gpu": False, "requires_node": False,
        "dependency_complexity": "moderate",
        "code_quality": 4, "doc_quality": 4, "match_score": 4.0,
        "overall_score": 4.0, "verdict": "install_now",
        "reason": "创新设计：AI Agent 通过 MCP 管理俱乐部到策略持续进化；Go 二进制部署简单；FM 风格数据模型可借鉴（32+19 隐藏属性）；需要安装 Go 1.26+",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["MCP", "足球经理", "AI Agent", "Go", "模拟"]
    },
    {
        "url": "https://github.com/the4chancup/4ccEditor",
        "name": "4ccEditor",
        "description": "PES 存档编辑器——支持 PES 2015-2021，球队跨版本移植，AATF 自动美化。C++/MSVC，zlib 协议",
        "category": "足球分析", "subcategory": "PES工具",
        "language": "C++", "stars": 12, "last_commit_days": 100,
        "has_readme": True, "has_demo": True, "has_dockerfile": False,
        "requires_gpu": False, "requires_node": False,
        "dependency_complexity": "simple",
        "code_quality": 3, "doc_quality": 2, "match_score": 3.5,
        "overall_score": 3.5, "verdict": "worth_testing",
        "reason": "Windows 原生 GUI 工具，即装即用；直接操作 PES 存档（与用户数据生态相关）；PES 社区唯一活跃维护的编辑器；局限：仅支持到 PES 2021",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["PES", "存档编辑", "Windows", "工具"]
    },
    {
        "url": "https://github.com/edyeftimie/FootballMangerPlayers",
        "name": "FootballMangerPlayers",
        "description": "足球游戏球员属性编辑器——FIFA/EAFC/PES 支持，C++/Qt GUI，MVC 架构",
        "category": "足球分析", "subcategory": "球员编辑",
        "language": "C++", "stars": 3, "last_commit_days": 283,
        "has_readme": True, "has_demo": False, "has_dockerfile": False,
        "requires_gpu": False, "requires_node": False,
        "dependency_complexity": "complex",
        "code_quality": 2, "doc_quality": 2, "match_score": 1.5,
        "overall_score": 1.2, "verdict": "skip",
        "reason": "9个月无更新（2024年10月最后提交）；需要 Qt 框架；文档简陋；功能与 4ccEditor 重叠但更差；不值得花时间安装测试",
        "evaluated_at": datetime.now().isoformat(),
        "tags": ["FIFA", "PES", "Qt", "废弃"]
    },
]

save_db(evaluations)

# Print summary
print("=" * 70)
print(f"评估完成: {len(evaluations)} 个项目已写入 evaluations.json")
print("=" * 70)
print()
icons = {"install_now": "[INSTALL]", "worth_testing": "[TEST]   ", "reference_only": "[REF]    ", "skip": "[SKIP]   "}
for e in sorted(evaluations, key=lambda x: -x["overall_score"]):
    icon = icons.get(e["verdict"], "[?]     ")
    print(f"{icon} {e['overall_score']:.1f}/5  {e['name']:35s} [{e['category']}]")
    print(f"        {e['reason'][:150]}")
    print()

# Stats
cats = {}
for e in evaluations:
    v = e["verdict"]
    cats[v] = cats.get(v, 0) + 1
print("=" * 70)
print(f"裁决分布: INSTALL={cats.get('install_now',0)} | TEST={cats.get('worth_testing',0)} | REF={cats.get('reference_only',0)} | SKIP={cats.get('skip',0)}")
