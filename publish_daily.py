#!/usr/bin/env python3
"""
每日一键发布：评估 → 增强 → 提交 → 推送

用法：
  python publish_daily.py --date 2026-07-21
  python publish_daily.py --date 2026-07-21 --skip-eval   # 跳过重新评估
  python publish_daily.py --date 2026-07-21 --dry-run     # 只生成不推送
"""
import json, sys, subprocess
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

ROOT = Path(__file__).parent
REPORT_SOURCE = Path(r"F:\Obsidian\小毛驴\信息简报\工作周报")
EVALS_DB = Path(r"E:\AI\football\evaluations.json")


def run(cmd: list, cwd=None):
    """Run a command, print output, return success."""
    print(f"  → {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or str(ROOT))
    if result.returncode != 0:
        print(f"  ✗ FAILED: {result.stderr[:200]}")
        return False
    if result.stdout.strip():
        print(f"  ✓ {result.stdout.strip()[:120]}")
    return True


def main():
    parser = ArgumentParser(description="Publish daily report to GitHub")
    parser.add_argument("--date", required=True, help="Date YYYY-MM-DD")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    date = args.date
    report_file = f"{date}-Github日报.md"
    source_path = REPORT_SOURCE / report_file
    dest_path = ROOT / report_file

    print(f"📋 发布日报: {date}")
    print(f"   源文件: {source_path}")

    # Step 1: Check source exists
    if not source_path.exists():
        print(f"\n❌ 日报未生成: {source_path}")
        print("   请先用 Claude Code 生成日报")
        sys.exit(1)

    # Step 2: Copy to publish directory
    print(f"\n[1/4] 复制日报到发布目录...")
    content = source_path.read_text(encoding="utf-8")
    dest_path.write_text(content, encoding="utf-8")
    print(f"  ✓ 已复制 ({len(content)} 字符)")

    # Step 3: Evaluate projects (skip if requested)
    if not args.skip_eval:
        print(f"\n[2/4] 评估项目...")
        # Check if evaluations already exist
        if EVALS_DB.exists():
            evals = json.loads(EVALS_DB.read_text(encoding="utf-8"))
            today_evals = [e for e in evals if e.get("evaluated_at", "").startswith(date)]
            if today_evals:
                print(f"  ✓ 今日已有 {len(today_evals)} 条评估，跳过")
            else:
                print(f"  ⚠ 今日无评估记录，请先运行 batch_evaluate.py")
        else:
            print(f"  ⚠ 评估数据库不存在")
    else:
        print(f"\n[2/4] 跳过评估 (--skip-eval)")

    # Step 4: Enhance report with scores
    print(f"\n[3/4] 注入评分...")
    sys.path.insert(0, str(ROOT))
    from enhance_report import load_evals_db, enhance_report_v2

    evals = load_evals_db()
    enhanced = enhance_report_v2(content, evals)
    dest_path.write_text(enhanced, encoding="utf-8")
    print(f"  ✓ 增强版已写入 ({len(enhanced)} 字符)")

    # Update README with latest report
    readme_lines = []
    readme_path = ROOT / "README.md"
    existing = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

    # Simple README update: add link to today's report
    today_entry = f"- [{date}]({report_file})"
    if today_entry not in existing:
        # Insert after "## 目录" section
        if "## 目录" in existing:
            existing = existing.replace(
                "## 目录\n",
                f"## 目录\n\n{today_entry}\n"
            )
        readme_path.write_text(existing, encoding="utf-8")

    # Step 5: Commit and push
    if not args.dry_run:
        print(f"\n[4/4] 提交并推送...")
        if not run(["git", "add", "-A"]):
            sys.exit(1)
        if not run(["git", "commit", "-m", f"日报 {date} — 含 {len(evals)} 个项目评分"]):
            # Empty commit is OK (no changes)
            print("  (无变更，跳过提交)")
        if not run(["git", "push"]):
            print("  ⚠ 推送失败，请检查网络")
    else:
        print(f"\n[4/4] DRY RUN — 跳过推送")

    print(f"\n✅ 发布完成: https://github.com/babymcsd/github-trending-daily")
    print(f"   日报: {report_file}")


if __name__ == "__main__":
    main()
