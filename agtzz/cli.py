"""CLI 接口"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agtzz.core import FileOrganizer, ActionLog, batch_rename, find_duplicates


def cmd_scan(args: argparse.Namespace) -> int:
    """扫描目录"""
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"错误：目录不存在 {target}", file=sys.stderr)
        return 1

    organizer = FileOrganizer(dry_run=True)
    files = organizer.scan(target, recursive=not args.no_recursive)

    print(f"\n📁 目录 {target} 中共发现 {len(files)} 个文件：\n")
    stats = organizer.get_stats(target)
    for category, count in sorted(stats.items()):
        print(f"  📂 {category:20} {count} 个文件")

    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    """预览整理方案"""
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"错误：目录不存在 {target}", file=sys.stderr)
        return 1

    organizer = FileOrganizer(dry_run=True)
    actions = organizer.preview(target)
    warnings = organizer.get_warnings()

    if not actions:
        print("\n未发现需要整理的文件。")
        return 0

    print(f"\n📋 整理方案预览（共 {len(actions)} 个文件）\n")
    
    if warnings:
        print("⚠️  警告：")
        for w in warnings[:5]:
            print(f"   • {w}")
        if len(warnings) > 5:
            print(f"   ... 还有 {len(warnings) - 5} 个警告")
        print()

    # 显示完整路径
    for action in actions:
        src_name = Path(action["source"]).name
        src_dir = Path(action["source"]).parent
        dst_path = Path(action["destination"])
        dst_name = dst_path.name
        dst_dir = dst_path.parent
        
        print(f"  {src_dir.name}/{src_name}")
        print(f"    ↓")
        print(f"  {dst_dir}/{dst_name}  ({action['category']})")
        if action.get("conflict"):
            print(f"    ⚠️  {action['conflict']}")
        print()

    return 0


def cmd_organize(args: argparse.Namespace) -> int:
    """执行整理"""
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"错误：目录不存在 {target}", file=sys.stderr)
        return 1

    log = ActionLog()
    organizer = FileOrganizer(dry_run=not args.force, log=log)
    actions = organizer.organize(target)
    stats = organizer.get_move_stats()
    warnings = organizer.get_warnings()

    if warnings:
        print("⚠️  警告：")
        for w in warnings:
            print(f"   • {w}")
        print()

    if not args.force:
        print(f"\n📋 预览模式：共 {len(actions)} 个文件待整理\n")
        for action in actions[:10]:
            src = Path(action["source"]).name
            dst = Path(action["destination"])
            print(f"  {src:30} → {dst}")
        if len(actions) > 10:
            print(f"  ... 还有 {len(actions) - 10} 个文件")
        print("\n如需实际执行，请添加 --force 参数")
    else:
        print(f"\n✅ 整理完成！")
        print(f"   已移动: {stats['moved']} 个文件")
        print(f"   已跳过: {stats['skipped']} 个文件")
        if stats['errors']:
            print(f"   错误: {len(stats['errors'])} 个")
            for err in stats['errors'][:5]:
                print(f"     • {err}")

    return 0


def cmd_duplicate(args: argparse.Namespace) -> int:
    """查找重复文件"""
    target = Path(args.directory).resolve()
    if not target.exists():
        print(f"错误：目录不存在 {target}", file=sys.stderr)
        return 1

    duplicates = find_duplicates(target, recursive=not args.no_recursive)

    if not duplicates:
        print("\n✅ 未发现重复文件。")
        return 0

    print(f"\n🔍 发现 {len(duplicates)} 组重复文件：\n")
    total_dup = sum(len(g) for g in duplicates)
    print(f"共 {total_dup} 个重复文件\n")
    
    for i, group in enumerate(duplicates, 1):
        size = group[0].stat().st_size if group else 0
        size_str = f" ({size // 1024} KB)" if size > 1024 else ""
        print(f"组 {i}{size_str} ({len(group)} 个文件):")
        for path in group:
            print(f"  • {path}")
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

    if not renamed:
        print("\n未找到需要重命名的文件。")
        return 0

    print(f"\n📝 找到 {len(renamed)} 个需要重命名的文件：\n")
    for old, new in renamed[:10]:
        print(f"  {old.name:30} → {new.name}")
    
    if len(renamed) > 10:
        print(f"  ... 还有 {len(renamed) - 10} 个")
        print()
        print("（仅显示前10个）")

    if args.dry_run:
        print("\n（预览模式，未实际执行）")
    else:
        confirm = input("\n确认执行？(y/N) ")
        if confirm.lower() == "y":
            for old, new in renamed:
                if old != new:
                    old.rename(new)
            print(f"\n✅ 已重命名 {len(renamed)} 个文件。")
        else:
            print("\n已取消。")

    return 0


def cmd_log(args: argparse.Namespace) -> int:
    """显示操作日志"""
    log_file = Path.home() / ".agtzz" / "actions.jsonl"
    
    if not log_file.exists():
        print("\n暂无操作日志。")
        return 0
    
    print(f"\n📜 最近的操作日志（{log_file}）：\n")
    
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for line in lines[-10:]:
        try:
            entry = json.loads(line)
            ts = entry.get("timestamp", "")[:19]
            action = entry.get("action", "")
            src = Path(entry.get("source", "")).name
            dst = entry.get("destination", "")
            error = entry.get("error", "")
            
            if error:
                print(f"  [{ts}] ❌ {action}: {src} - {error}")
            elif dst:
                print(f"  [{ts}] {action}: {src} → {Path(dst).name}")
            else:
                print(f"  [{ts}] {action}: {src}")
        except json.JSONDecodeError:
            print(f"  [错误] 无法解析日志行")
    
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    """回滚最后一条操作"""
    log = ActionLog()
    entries = log.get_entries(limit=1)
    
    if not entries:
        print("\n没有可回滚的操作。")
        return 0
    
    last = entries[0]
    print(f"\n🔄 准备回滚最后一条操作：")
    print(f"   类型: {last['action']}")
    print(f"   时间: {last['timestamp']}")
    print(f"   源: {last['source']}")
    print(f"   目标: {last.get('destination', 'N/A')}")
    
    if not args.force:
        confirm = input("\n确认回滚？(y/N) ")
        if confirm.lower() != "y":
            print("已取消。")
            return 0
    
    rolled_back = log.rollback()
    if rolled_back:
        print("\n✅ 回滚成功。")
    else:
        print("\n❌ 回滚失败。")
    
    return 0


def main(argv: list[str] | None = None) -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="agtzz",
        description="智能文件整理工具 - 安全、可预览、可回滚",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="agtzz 0.2.0",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan
    scan_parser = subparsers.add_parser("scan", help="扫描目录")
    scan_parser.add_argument("directory", help="目标目录")
    scan_parser.add_argument(
        "--no-recursive", action="store_true", help="不递归子目录"
    )

    # preview
    preview_parser = subparsers.add_parser(
        "preview", help="预览整理方案（默认模式）"
    )
    preview_parser.add_argument("directory", help="目标目录")

    # organize
    organize_parser = subparsers.add_parser(
        "organize", help="执行文件整理（默认预览模式）"
    )
    organize_parser.add_argument("directory", help="目标目录")
    organize_parser.add_argument(
        "--force", action="store_true", help="跳过确认直接执行"
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

    # log
    log_parser = subparsers.add_parser("log", help="查看操作日志")

    # rollback
    rollback_parser = subparsers.add_parser(
        "rollback", help="回滚最后一条操作"
    )
    rollback_parser.add_argument(
        "--force", action="store_true", help="跳过确认"
    )

    args = parser.parse_args(argv)

    commands = {
        "scan": cmd_scan,
        "preview": cmd_preview,
        "organize": cmd_organize,
        "duplicate": cmd_duplicate,
        "rename": cmd_rename,
        "log": cmd_log,
        "rollback": cmd_rollback,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
