#!/usr/bin/env python3
"""
每日一键发布：从旧系统读取合并版日报 → GitHub

旧系统目录: F:\Obsidian\小毛驴\信息简报\Github日报\  (主源，推 Gitee)
GitHub 仓库: github.com/babymcsd/github-trending-daily    (公开镜像)

用法：
  python publish_daily.py --date 2026-07-21            # 发布当天
  python publish_daily.py --date 2026-07-21 --dry-run  # 只复制不推送
"""
import sys, subprocess, shutil
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

# Windows UTF-8 fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
REPORT_SOURCE = Path(r"F:\Obsidian\小毛驴\信息简报\Github日报")  # 旧系统主目录


def run(cmd: list, cwd=None):
    """Run a command, print output, return success."""
    print(f"  → {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or str(ROOT))
    if result.returncode != 0:
        print(f"  - FAILED: {result.stderr[:200]}")
        return False
    if result.stdout.strip():
        print(f"  OK: {result.stdout.strip()[:120]}")
    return True


def main():
    parser = ArgumentParser(description="发布日报到 GitHub 公开仓库")
    parser.add_argument("--date", required=True, help="Date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    date = args.date
    source_file = f"{date}.md"                        # 旧系统: 2026-07-21.md
    dest_file = f"{date}-Github日报.md"               # GitHub: 2026-07-21-Github日报.md
    source_path = REPORT_SOURCE / source_file
    dest_path = ROOT / dest_file

    print(f"[Publish] {date}")
    print(f"   Source (Gitee): {source_path}")
    print(f"   Mirror (GitHub): {dest_path}")

    # Step 1: Check source exists
    if not source_path.exists():
        print(f"\n[ERROR] Report not found: {source_path}")
        print("   Run merge_reports.py first")
        sys.exit(1)

    # Step 2: Copy merged report to GitHub publish directory
    print(f"\n[1/3] Copy report...")
    content = source_path.read_text(encoding="utf-8")
    dest_path.write_text(content, encoding="utf-8")
    print(f"  {len(content)} chars copied")

    # Step 3: Copy contact.md
    contact_src = REPORT_SOURCE / "contact.md"
    if contact_src.exists():
        contact_dst = ROOT / "contact.md"
        shutil.copy(contact_src, contact_dst)
        print(f"  contact.md synced")

    # Step 4: Update README
    print(f"\n[2/3] Update README...")
    readme_path = ROOT / "README.md"
    existing = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    today_entry = f"- [{date}]({dest_file})"
    if today_entry not in existing and "## 目录" in existing:
        existing = existing.replace("## 目录\n", f"## 目录\n\n{today_entry}\n")
        readme_path.write_text(existing, encoding="utf-8")
        print(f"  Entry added")
    else:
        print(f"  (already exists)")

    # Step 5: Commit and push
    if not args.dry_run:
        print(f"\n[3/3] Commit and push to GitHub...")
        if not run(["git", "add", "-A"]):
            sys.exit(1)
        if not run(["git", "commit", "-m", f"Daily {date} - with email + football + scores"]):
            print("  (no changes)")
        if not run(["git", "push"]):
            print("  WARN: push failed, check network")
    else:
        print(f"\n[3/3] DRY RUN - skip push")

    print(f"\n[DONE] Published {date}")
    print(f"   Gitee: https://gitee.com/babymc/little-donkey-knowledge-base")
    print(f"   GitHub: https://github.com/babymcsd/github-trending-daily")


if __name__ == "__main__":
    main()
