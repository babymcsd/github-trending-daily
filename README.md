# GitHub Trending 日报

每日自动抓取 GitHub Trending 项目，附个性化评估打分。

## 特色

- 📊 **自动评分** — 每个项目基于用户环境（Windows / 无GPU / 公司网络）自动评估
- 🎯 **四层漏斗** — 元数据速筛 → 代码深度阅读 → 沙箱快测 → 深度试用
- ⚽ **足球 AI 专题** — 每日深度覆盖 AI × 足球统计/分析项目
- 🔍 **分类速览** — AI/ML、开发工具、基础设施、数据工程、安全

## 评分体系

| 评分 | 含义 | 行动 |
|------|------|------|
| 🟢 4.0+ | 高度匹配 | 立即安装测试 |
| 🟡 3.0-3.9 | 值得关注 | 列入测试队列 |
| 🔵 2.0-2.9 | 参考价值 | 学习架构/思路 |
| 🔴 <2.0 | 不推荐 | 跳过 |

评分基于用户画像：Windows 11 · Python 3.12 · 无 GPU · 无 Docker · 公司网络环境。

## 目录

- [2026-07-21](2026-07-21-Github日报.md) — 本地优先趋势 · AI 足球项目涌现 · Ghost Account 安全预警

## 架构

```
daily-reports/
├── README.md                    ← 你在这里
├── 2026-07-21-Github日报.md     ← 日报（含评分附录）
├── evaluator.py                 ← 评估引擎
└── .github/workflows/           ← 自动发布（计划中）
```

## 致谢

- 数据源：GitHub Trending / Trendshift / OSSInsight
- 评分引擎：自研 `evaluator.py`
- 生成工具：Claude Code

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
