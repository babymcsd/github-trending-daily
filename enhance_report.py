#!/usr/bin/env python3
"""
日报增强器：给每日 GitHub 日报的项目自动附加评估分数和测试结果。

用法：
  python enhance_report.py --date 2026-07-21
  python enhance_report.py --date 2026-07-21 --publish  # 输出到发布目录
"""
import json, re, sys
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

# Paths
REPORT_DIR = Path(r"F:\Obsidian\小毛驴\信息简报\工作周报")
EVALS_DB = Path(r"E:\AI\football\evaluations.json")
PUBLISH_DIR = Path(r"E:\AI\football\daily-reports")  # GitHub 发布目录

# Score badges
BADGES = {
    "install_now": "🟢 **{score:.1f}/5**",
    "worth_testing": "🟡 **{score:.1f}/5**",
    "reference_only": "🔵 **{score:.1f}/5**",
    "skip": "🔴 **{score:.1f}/5**",
}

VERDICT_CN = {
    "install_now": "推荐安装",
    "worth_testing": "值得测试",
    "reference_only": "仅供参考",
    "skip": "暂不推荐",
}


def load_evals_db() -> dict:
    """Load evaluations database, keyed by repo name (lowercase)."""
    if not EVALS_DB.exists():
        return {}
    data = json.loads(EVALS_DB.read_text(encoding="utf-8"))
    db = {}
    for e in data:
        # Key by repo name extracted from URL
        url = e.get("url", "")
        # Extract owner/repo from GitHub URL
        m = re.search(r'github\.com/([^/]+/[^/]+)', url)
        if m:
            key = m.group(1).lower()
            db[key] = e
        # Also key by just repo name
        name = e.get("name", "").lower()
        if name:
            db[name] = e
    return db


def enhance_report(report_text: str, evals: dict) -> str:
    """Insert evaluation badges after each GitHub project reference."""
    lines = report_text.split("\n")
    enhanced = []

    for line in lines:
        enhanced.append(line)

        # Find GitHub links in this line
        matches = list(re.finditer(r'\[([^\]]+)\]\(https://github\.com/([^\)]+)\)', line))
        for m in matches:
            repo_full = m.group(2).rstrip("/")  # e.g. "gangtao/AgentPitch"
            repo_name = repo_full.split("/")[-1].lower()

            # Look up evaluation
            eval_data = evals.get(repo_full.lower()) or evals.get(repo_name)

            if eval_data:
                verdict = eval_data.get("verdict", "")
                score = eval_data.get("overall_score", 0)
                badge_template = BADGES.get(verdict, "⚪ {score:.1f}/5")
                badge = badge_template.format(score=score)
                reason = eval_data.get("reason", "")
                vcn = VERDICT_CN.get(verdict, verdict)

                # Append evaluation line
                indent = " " * (len(line) - len(line.lstrip()))
                eval_line = f"\n{indent}> 📊 评估: {badge} — **{vcn}**"

                # Add match score details if available
                if eval_data.get("sandbox_tested"):
                    sandbox = eval_data["sandbox_result"]
                    eval_line += f" | 沙箱: {'✅' if sandbox == 'passed' else '⚠️'} {sandbox}"

                eval_line += "\n"
                if reason:
                    eval_line += f"{indent}> 💬 {reason[:200]}\n"

                # Only add if not already present (avoid duplicating)
                # Check if the next line already has an evaluation
                next_idx = lines.index(line) + 1 if line in lines else -1
                # Actually, let's just append after any link that has an eval
                enhanced.append(eval_line.rstrip())

    return "\n".join(enhanced)


def enhance_report_v2(report_text: str, evals: dict) -> str:
    """Version 2: Cleaner approach - add a score summary section per project,
    and also add inline badges to project names in detailed descriptions."""
    lines = report_text.split("\n")
    result = []
    project_scores_found = []

    for line in lines:
        # Detect project entries in the detailed football section
        # Pattern: "#### N. project-name — description"
        detailed_match = re.match(r'^(#{2,4}\s+\d+\.\s+)(.+)$', line)

        # Find any GitHub links
        gh_links = re.findall(r'\[([^\]]+)\]\(https://github\.com/([^\)]+)\)', line)

        if gh_links and not line.strip().startswith(">"):  # Don't modify blockquotes
            modified_line = line
            for link_text, repo_path in gh_links:
                repo_full = repo_path.rstrip("/")
                repo_name = repo_full.split("/")[-1].lower()
                eval_data = evals.get(repo_full.lower()) or evals.get(repo_name)

                if eval_data:
                    score = eval_data.get("overall_score", 0)
                    verdict = eval_data.get("verdict", "")
                    badge_emoji = {"install_now": "🟢", "worth_testing": "🟡",
                                   "reference_only": "🔵", "skip": "🔴"}.get(verdict, "⚪")

                    # Add score badge after the link
                    score_tag = f" `[{badge_emoji}{score:.1f}]`"
                    modified_line = modified_line.replace(
                        f"[{link_text}](https://github.com/{repo_path})",
                        f"[{link_text}](https://github.com/{repo_path}){score_tag}"
                    )
                    project_scores_found.append({
                        "name": link_text,
                        "score": score,
                        "verdict": verdict,
                        "reason": eval_data.get("reason", ""),
                        "repo": repo_full,
                    })

            result.append(modified_line)
        else:
            result.append(line)

    # Inject visitor counter after "生成时间" line
    date_match = re.search(r'生成时间：(\d{4}-\d{2}-\d{2})', "\n".join(result))
    counter_date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
    counter_badge = f"> ![Visitors](https://visitor-badge.laobi.icu/badge?page_id=babymcsd.github-trending-daily&date={counter_date})"
    new_result = []
    for line in result:
        new_result.append(line)
        if line.strip().startswith("> 生成时间"):
            new_result.append(counter_badge)
    result = new_result

    # Append evaluation summary section before "行动建议" if we found scores
    final = "\n".join(result)

    if project_scores_found:
        summary = [
            "",
            "---",
            "",
            "## 📊 项目评估附录（自动评分）",
            "",
            "> 评分引擎: `evaluator.py` · 四层漏斗（元数据→代码深度→沙箱→深度试用）",
            "> 用户画像: Windows 11, Python 3.12, 无GPU, 无Docker, 公司网络",
            "",
            "| 项目 | 评分 | 裁决 | 理由 |",
            "|------|------|------|------|",
        ]

        for p in sorted(project_scores_found, key=lambda x: -x["score"]):
            emoji = {"install_now": "🟢", "worth_testing": "🟡",
                     "reference_only": "🔵", "skip": "🔴"}.get(p["verdict"], "⚪")
            vcn = VERDICT_CN.get(p["verdict"], p["verdict"])
            reason_short = p["reason"][:80] + "..." if len(p["reason"]) > 80 else p["reason"]
            summary.append(f"| [{p['name']}](https://github.com/{p['repo']}) | {emoji} {p['score']:.1f}/5 | {vcn} | {reason_short} |")

        summary.append("")
        summary.append(f"> 共评估 {len(project_scores_found)} 个项目 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Insert after the last section before 行动建议 or at end
        if "## 五、行动建议" in final:
            final = final.replace("## 五、行动建议", "\n".join(summary) + "\n\n## 五、行动建议")
        else:
            final += "\n".join(summary)

    return final


def main():
    parser = ArgumentParser(description="Enhance daily report with evaluation scores")
    parser.add_argument("--date", type=str, required=True, help="Date YYYY-MM-DD")
    parser.add_argument("--publish", action="store_true", help="Output to publish directory")
    args = parser.parse_args()

    # Load evaluations
    evals = load_evals_db()
    print(f"Loaded {len(evals)} evaluations from database")

    # Read report
    report_path = REPORT_DIR / f"{args.date}-Github日报.md"
    if not report_path.exists():
        print(f"ERROR: Report not found: {report_path}")
        sys.exit(1)

    report_text = report_path.read_text(encoding="utf-8")
    print(f"Read report: {report_path.name} ({len(report_text)} chars)")

    # Enhance
    enhanced = enhance_report_v2(report_text, evals)

    # Write
    if args.publish:
        PUBLISH_DIR.mkdir(parents=True, exist_ok=True)
        out_path = PUBLISH_DIR / f"{args.date}-Github日报.md"
    else:
        out_path = REPORT_DIR / f"{args.date}-Github日报-评分版.md"

    out_path.write_text(enhanced, encoding="utf-8")
    print(f"Enhanced report written: {out_path}")

    # Also copy README.md for GitHub
    if args.publish:
        readme_path = PUBLISH_DIR / "README.md"
        readme_path.write_text(enhanced, encoding="utf-8")
        print(f"GitHub README written: {readme_path}")


if __name__ == "__main__":
    main()
