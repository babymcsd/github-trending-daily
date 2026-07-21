#!/usr/bin/env python3
"""
项目评估引擎 — 自动扫描 GitHub 项目，判断是否值得安装测试。

四层漏斗：
  1. 元数据速筛 (自动) → 2. 代码深度阅读 (Agent) → 3. 隔离沙箱快测 (自动) → 4. 深度试用 (人工)

用法：
  python evaluator.py --url https://github.com/xxx/yyy          # 单个项目
  python evaluator.py --batch today                              # 批量评估今日日报
  python evaluator.py --query "足球"                              # 查询已评估项目
  python evaluator.py --stats                                    # 评估统计
"""

import json, os, sys, re, time, subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
DB_PATH = Path(r"E:\AI\football\evaluations.json")
SANDBOX_DIR = Path(r"E:\AI\football\sandbox")
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# 用户环境画像
USER_PROFILE = {
    "os": "Windows 11",
    "python_version": "3.12",
    "has_gpu": False,
    "has_docker": False,
    "has_node": False,
    "corporate_network": True,  # 很多站点被拦截
    "disk_gb_free": 200,
    "ram_gb": 32,
}

# 用户兴趣权重（0-1，越高越关注）
INTEREST_WEIGHTS = {
    "AI/ML": 0.9,
    "数据工程": 0.85,
    "自动化/工作流": 0.8,
    "足球分析": 0.95,
    "开发工具": 0.7,
    "基础设施": 0.5,
    "安全": 0.3,
    "前端/UI": 0.1,
    "移动端": 0.1,
    "区块链/Web3": 0.0,
    "游戏模组": 0.2,
}

# ═══════════════════════════════════════
# DATA MODEL
# ═══════════════════════════════════════

@dataclass
class Evaluation:
    """一个项目的完整评估记录"""
    # 基础信息
    url: str
    name: str
    description: str = ""
    category: str = ""           # AI/ML, 开发工具, 足球分析, etc.
    subcategory: str = ""        # 足球预测, PES工具, LLM推理, etc.

    # 第 1 层：元数据
    language: str = ""
    stars: int = 0
    last_commit_days: int = 999   # 距今天数
    has_readme: bool = False
    has_requirements: bool = False
    has_dockerfile: bool = False
    has_demo: bool = False
    requires_gpu: bool = False
    requires_node: bool = False

    # 第 2 层：代码深度（Agent 评估后填充）
    code_quality: int = 0         # 0-5
    doc_quality: int = 0          # 0-5
    dependency_complexity: str = ""  # simple / moderate / complex / nightmare
    install_steps: int = 0        # 需要几步才能跑起来
    match_score: float = 0.0      # 和用户需求的匹配度 0-5

    # 第 3 层：沙箱测试
    sandbox_tested: bool = False
    sandbox_result: str = ""      # passed / failed / partial
    sandbox_errors: str = ""
    sandbox_time_seconds: int = 0

    # 综合
    overall_score: float = 0.0    # 0-5
    verdict: str = ""             # install_now / worth_testing / reference_only / skip
    reason: str = ""
    evaluated_at: str = ""
    tags: list = field(default_factory=list)


# ═══════════════════════════════════════
# LAYER 1: METADATA SCREENING
# ═══════════════════════════════════════

def layer1_screen(eval: Evaluation) -> Evaluation:
    """快速元数据筛选。用 WebFetch 获取到的信息填充。"""
    issues = []
    score = 5.0

    # 活跃度
    if eval.last_commit_days > 365:
        issues.append(f"🔴 最后更新 {eval.last_commit_days} 天前（>1年）")
        score -= 2.0
    elif eval.last_commit_days > 180:
        issues.append(f"🟡 最后更新 {eval.last_commit_days} 天前（>6月）")
        score -= 1.0
    elif eval.last_commit_days <= 30:
        score += 0.5  # 活跃加分

    # 文档
    if not eval.has_readme:
        issues.append("🔴 无 README")
        score -= 2.0

    # GPU 需求 vs 用户没有 GPU
    if eval.requires_gpu and not USER_PROFILE["has_gpu"]:
        issues.append("🔴 需要 GPU 但用户没有")
        score -= 3.0

    # Docker（对用户不适用——没装 Docker）
    if eval.has_dockerfile:
        issues.append("🟢 有 Dockerfile（网络允许的话可一键部署）")
        score += 0.3

    # Demo 存在
    if eval.has_demo:
        issues.append("🟢 有 Demo/示例代码")
        score += 0.5

    # 依赖复杂度估算
    if eval.dependency_complexity == "nightmare":
        score -= 1.5
    elif eval.dependency_complexity == "complex":
        score -= 0.5
    elif eval.dependency_complexity == "simple":
        score += 0.5

    # 兴趣匹配
    category_weight = INTEREST_WEIGHTS.get(eval.category, 0.3)
    score = score * (0.5 + 0.5 * category_weight)

    # 裁决
    score = max(0, min(5, score))
    eval.overall_score = round(score, 1)

    if score >= 4.0:
        eval.verdict = "install_now"
    elif score >= 3.0:
        eval.verdict = "worth_testing"
    elif score >= 2.0:
        eval.verdict = "reference_only"
    else:
        eval.verdict = "skip"

    eval.reason = "; ".join(issues) if issues else "通过全部元数据检查"
    eval.evaluated_at = datetime.now().isoformat()

    return eval


# ═══════════════════════════════════════
# LAYER 2: CODE DEEP READ (Agent-assisted)
# ═══════════════════════════════════════

def layer2_prompt(eval: Evaluation) -> str:
    """生成给 Agent 的代码深度评估提示词。"""
    return f"""评估这个 GitHub 项目的实际可用性。

项目: {eval.name}
URL: {eval.url}
类别: {eval.category}
描述: {eval.description}

用户环境:
- Windows 11, Python 3.12, 无 GPU, 无 Docker
- 公司网络（部分外站被拦）
- 兴趣: AI/ML工具, 足球分析, 数据工程, 自动化

请回答：
1. 代码质量 (0-5): 结构清晰？有测试？有注释？
2. 文档质量 (0-5): 新人能看懂？有完整 API 文档？
3. 依赖复杂度: simple(纯Python标准库) / moderate(<5个外部包) / complex(需要CUDA/特殊环境) / nightmare(几十个依赖+需要编译)
4. 安装步骤: 从 git clone 到跑起来需要几步？
5. 匹配度 (0-5): 这个项目对用户的实际价值？
   - 5=直接解决用户的日常需求
   - 3=参考价值，部分代码/思路可复用
   - 1=和用户需求无关
6. 最终建议: install_now / worth_testing / reference_only / skip

只输出 JSON:
{{"code_quality": X, "doc_quality": X, "dependency_complexity": "X", "install_steps": X, "match_score": X.X, "verdict": "X", "reason": "简短理由"}}"""


# ═══════════════════════════════════════
# LAYER 3: SANDBOX TEST
# ═══════════════════════════════════════

def layer3_sandbox(eval: Evaluation) -> Evaluation:
    """隔离沙箱自动化测试。"""
    eval.sandbox_tested = True

    project_dir = SANDBOX_DIR / eval.name
    venv_dir = project_dir / ".venv"

    t0 = time.time()

    try:
        # Step 1: Clone (already done or shallow clone)
        if not project_dir.exists():
            result = subprocess.run(
                ["git", "clone", "--depth=1", eval.url, str(project_dir)],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                eval.sandbox_result = "failed"
                eval.sandbox_errors = f"Clone failed: {result.stderr[:200]}"
                eval.sandbox_time_seconds = int(time.time() - t0)
                return eval

        # Step 2: Create venv
        if not venv_dir.exists():
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)],
                          capture_output=True, timeout=60)

        pip = str(venv_dir / "Scripts" / "pip.exe")
        python = str(venv_dir / "Scripts" / "python.exe")

        # Step 3: Install
        req_files = list(project_dir.glob("requirements*.txt")) + list(project_dir.glob("pyproject.toml"))
        if req_files:
            result = subprocess.run(
                [pip, "install", "-r", str(req_files[0])],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                eval.sandbox_result = "partial"
                eval.sandbox_errors = f"Install warning: {result.stderr[:200]}"

        # Step 4: Try to run demo/tests
        demo_files = (
            list(project_dir.glob("demo*.py")) +
            list(project_dir.glob("example*.py")) +
            list(project_dir.glob("test_*.py"))
        )
        if demo_files:
            result = subprocess.run(
                [python, str(demo_files[0])],
                capture_output=True, text=True, timeout=60,
                cwd=str(project_dir)
            )
            if result.returncode == 0:
                eval.sandbox_result = "passed"
            else:
                eval.sandbox_result = "partial"
                eval.sandbox_errors = f"Demo failed: {result.stderr[:200]}"
        else:
            eval.sandbox_result = "passed"  # 没有 demo 但安装成功也算过

    except subprocess.TimeoutExpired:
        eval.sandbox_result = "failed"
        eval.sandbox_errors = "Timeout"
    except Exception as e:
        eval.sandbox_result = "failed"
        eval.sandbox_errors = str(e)[:200]

    eval.sandbox_time_seconds = int(time.time() - t0)
    return eval


# ═══════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════

def load_db() -> list[dict]:
    if DB_PATH.exists():
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    return []


def save_db(evals: list[dict]):
    DB_PATH.write_text(json.dumps(evals, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_evaluation(eval: Evaluation):
    db = load_db()
    # Replace or append
    for i, item in enumerate(db):
        if item.get("url") == eval.url:
            db[i] = asdict(eval)
            save_db(db)
            return
    db.append(asdict(eval))
    save_db(db)


def query_evaluations(verdict: str = None, category: str = None,
                      min_score: float = 0, keyword: str = None) -> list[dict]:
    db = load_db()
    results = db
    if verdict:
        results = [e for e in results if e.get("verdict") == verdict]
    if category:
        results = [e for e in results if category.lower() in e.get("category", "").lower()]
    if min_score > 0:
        results = [e for e in results if e.get("overall_score", 0) >= min_score]
    if keyword:
        kw = keyword.lower()
        results = [e for e in results if
                   kw in e.get("name","").lower() or
                   kw in e.get("description","").lower() or
                   kw in str(e.get("tags",[])).lower()]
    return sorted(results, key=lambda x: -x.get("overall_score", 0))


def get_stats() -> dict:
    db = load_db()
    verdicts = {}
    categories = {}
    for e in db:
        v = e.get("verdict", "unknown")
        verdicts[v] = verdicts.get(v, 0) + 1
        c = e.get("category", "unknown")
        categories[c] = categories.get(c, 0) + 1
    return {
        "total": len(db),
        "by_verdict": verdicts,
        "by_category": categories,
        "avg_score": round(sum(e.get("overall_score",0) for e in db) / len(db), 1) if db else 0,
        "install_now": len([e for e in db if e.get("verdict") == "install_now"]),
        "worth_testing": len([e for e in db if e.get("verdict") == "worth_testing"]),
    }


# ═══════════════════════════════════════
# BATCH EVALUATION (from daily report)
# ═══════════════════════════════════════

def extract_projects_from_report(report_path: str) -> list[dict]:
    """从日报 Markdown 中提取项目列表。"""
    content = Path(report_path).read_text(encoding="utf-8")
    projects = []

    # 匹配 GitHub URL 行
    # 格式: - [项目名](https://github.com/xxx/yyy) — 描述 (语言, ★Stars)
    pattern = r'\[([^\]]+)\]\((https://github\.com/[^\)]+)\)[^—]*—\s*(.+?)(?:\s*\(([^)]+)\))?\s*$'

    for m in re.finditer(pattern, content, re.MULTILINE):
        name = m.group(1)
        url = m.group(2)
        desc = m.group(3).strip()
        meta = m.group(4) or ""

        # Parse language and stars
        language = ""
        stars = 0
        star_match = re.search(r'★\s*([\d,]+)', meta)
        if star_match:
            stars = int(star_match.group(1).replace(",", ""))
        lang_match = re.search(r'^([A-Za-z+#]+)', meta)
        if lang_match:
            language = lang_match.group(1)

        # Determine category from section header context
        category = "unknown"
        # Find which section this project falls under
        pos = m.start()
        section_text = content[:pos]
        section_match = re.findall(r'^##?\s+(.+?)$', section_text, re.MULTILINE)
        if section_match:
            last_section = section_match[-1].lower()
            if "足球" in last_section or "football" in last_section:
                category = "足球分析"
            elif "ai" in last_section or "ml" in last_section or "模型" in last_section:
                category = "AI/ML"
            elif "工具" in last_section or "dev" in last_section or "开发" in last_section:
                category = "开发工具"
            elif "数据" in last_section or "data" in last_section:
                category = "数据工程"
            elif "基础" in last_section or "infra" in last_section:
                category = "基础设施"
            elif "安全" in last_section or "security" in last_section:
                category = "安全"

        projects.append({
            "name": name.strip(),
            "url": url.strip(),
            "description": desc.strip(),
            "language": language,
            "stars": stars,
            "category": category,
        })

    return projects


# ═══════════════════════════════════════
# CLI
# ═══════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="项目评估引擎")
    parser.add_argument("--url", type=str, help="评估单个 GitHub 项目")
    parser.add_argument("--batch", type=str, help="批量评估: 'today' 或日报路径")
    parser.add_argument("--query", type=str, help="查询已评估项目（关键词）")
    parser.add_argument("--verdict", type=str, choices=["install_now","worth_testing","reference_only","skip"])
    parser.add_argument("--category", type=str)
    parser.add_argument("--min-score", type=float, default=0)
    parser.add_argument("--stats", action="store_true", help="显示评估统计")
    parser.add_argument("--export", type=str, help="导出评估结果到 JSON 文件")
    args = parser.parse_args()

    if args.stats:
        stats = get_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return

    if args.query or args.verdict or args.category:
        results = query_evaluations(
            verdict=args.verdict,
            category=args.category,
            min_score=args.min_score,
            keyword=args.query,
        )
        if args.export:
            Path(args.export).write_text(
                json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Exported {len(results)} evaluations to {args.export}")
        else:
            for r in results:
                print(f"[{r['verdict']:15s}] {r['overall_score']:.1f}/5  {r['name']:30s}  {r['category']}")
                if r.get('reason'):
                    print(f"                    {r['reason'][:120]}")
                print()
        return

    if args.batch:
        if args.batch == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            report_path = Path(rf"F:\Obsidian\小毛驴\信息简报\工作周报\{today}-Github日报.md")
        else:
            report_path = Path(args.batch)

        if not report_path.exists():
            print(f"Report not found: {report_path}")
            return

        projects = extract_projects_from_report(str(report_path))
        print(f"Extracted {len(projects)} projects from {report_path.name}")
        for p in projects:
            print(f"  [{p['category']:12s}] {p['name']:30s} {p['url']}")

        # TODO: Feed into layer1_screen for each project
        # For now, just extract and display
        return

    if args.url:
        eval = Evaluation(url=args.url, name=args.url.split("/")[-1])
        eval = layer1_screen(eval)
        upsert_evaluation(eval)
        print(json.dumps(asdict(eval), ensure_ascii=False, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
