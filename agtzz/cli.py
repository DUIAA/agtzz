"""CLI 接口"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agtzz.core import FileOrganizer, batch_rename, find_duplicates


def cmd_scan(args: argparse.Namespace) -> int:
    """扫描目录"""
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"错误：目录不存在 {target}", file=sys.stderr)
        return 1

    organizer = FileOrganizer(dry_run=True)
    files = organizer.scan(target, recursive=not args.no_recursive)

    print(f"\n目录 {target} 中共发现 {len(files)} 个文件：\n")
    stats = organizer.get_stats(target)
    for category, count in sorted(stats.items()):
        print(f"  {category}: {count}")

    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    """预览整理方案"""
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"错误：目录不存在 {target}", file=sys.stderr)
        return 1

    organizer = FileOrganizer(dry_run=True)
    actions = organizer.preview(target)

    print(f"\n整理方案预览（{len(actions)} 个文件）：\n")
    for action in actions[:20]:  # 只显示前20个
        src = Path(action["source"]).name
        dst = action["category"]
        print(f"  {src:30} -> {dst}/")

    if len(actions) > 20:
        print(f"  ... 还有 {len(actions) - 20} 个文件")

    return 0


def cmd_organize(args: argparse.Namespace) -> int:
    """执行整理"""
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"错误：目录不存在 {target}", file=sys.stderr)
        return 1

    organizer = FileOrganizer(dry_run=args.dry_run)
    actions = organizer.organize(target)

    print(f"\n整理完成！共处理 {len(actions)} 个文件。")
    if args.dry_run:
        print("（预览模式，未实际移动文件）")

    return 0


def cmd_duplicate(args: argparse.Namespace) -> int:
    """查找重复文件"""
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"错误：目录不存在 {target}", file=sys.stderr)
        return 1

    duplicates = find_duplicates(target, recursive=not args.no_recursive)

    if not duplicates:
        print("\n未发现重复文件。")
        return 0

    print(f"\n发现 {len(duplicates)} 组重复文件：\n")
    for i, group in enumerate(duplicates, 1):
        print(f"组 {i} ({len(group)} 个文件):")
        for path in group:
            print(f"  - {path}")
        print()

    return 0


def cmd_rename(args: argparse.Namespace) -> int:
    """批量重命名"""
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"错误：目录不存在 {target}", file=sys.stderr)
        return 1

    renamed = batch_rename(
        target, args.old_prefix, args.new_prefix
    )

    print(f"\n找到 {len(renamed)} 个需要重命名的文件：")
    for old, new in renamed[:10]:
        print(f"  {old.name} -> {new.name}")

    if len(renamed) > 10:
        print(f"  ... 还有 {len(renamed) - 10} 个")

    if not args.dry_run:
        confirm = input("\n确认执行？(y/N) ")
        if confirm.lower() == "y":
            for old, new in renamed:
                if old != new:
                    old.rename(new)
            print(f"已重命名 {len(renamed)} 个文件。")
        else:
            print("已取消。")

    return 0


def main(argv: list[str] | None = None) -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="agtzz",
        description="智能文件整理工具",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="agtzz 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan
    scan_parser = subparsers.add_parser("scan", help="扫描目录")
    scan_parser.add_argument("directory", help="目标目录")
    scan_parser.add_argument(
        "--no-recursive", action="store_true", help="不递归子目录"
    )

    # preview
    preview_parser = subparsers.add_parser("preview", help="预览整理方案")
    preview_parser.add_argument("directory", help="目标目录")

    # organize
    organize_parser = subparsers.add_parser(
        "organize", help="执行文件整理"
    )
    organize_parser.add_argument("directory", help="目标目录")
    organize_parser.add_argument(
        "--dry-run", action="store_true", help="预览模式，不实际执行"
    )

    # duplicate
    dup_parser = subparsers.add_parser(
        "duplicate", help="查找重复文件"
    )
    dup_parser.add_argument("directory", help="目标目录")
    dup_parser.add_argument(
        "--no-recursive", action="store_true", help="不递归子目录"
    )

    # rename
    rename_parser = subparsers.add_parser(
        "rename", help="批量重命名"
    )
    rename_parser.add_argument("directory", help="目标目录")
    rename_parser.add_argument(
        "--old-prefix", required=True, help="原前缀"
    )
    rename_parser.add_argument(
        "--new-prefix", required=True, help="新前缀"
    )
    rename_parser.add_argument(
        "--dry-run", action="store_true", help="预览模式"
    )

    args = parser.parse_args(argv)

    commands = {
        "scan": cmd_scan,
        "preview": cmd_preview,
        "organize": cmd_organize,
        "duplicate": cmd_duplicate,
        "rename": cmd_rename,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
