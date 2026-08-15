"""文件整理核心逻辑"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 默认分类规则：扩展名 -> 文件夹名
DEFAULT_CATEGORIES: dict[str, str] = {
    # 图片
    ".jpg": "images",
    ".jpeg": "images",
    ".png": "images",
    ".gif": "images",
    ".bmp": "images",
    ".svg": "images",
    ".webp": "images",
    ".tiff": "images",
    # 文档
    ".pdf": "documents",
    ".doc": "documents",
    ".docx": "documents",
    ".txt": "documents",
    ".rtf": "documents",
    ".odt": "documents",
    ".md": "documents",
    ".tex": "documents",
    # 电子表格
    ".xls": "spreadsheets",
    ".xlsx": "spreadsheets",
    ".csv": "spreadsheets",
    ".ods": "spreadsheets",
    # 演示文稿
    ".ppt": "presentations",
    ".pptx": "presentations",
    ".odp": "presentations",
    # 压缩包
    ".zip": "archives",
    ".rar": "archives",
    ".7z": "archives",
    ".tar": "archives",
    ".gz": "archives",
    # 音频
    ".mp3": "audio",
    ".wav": "audio",
    ".flac": "audio",
    ".aac": "audio",
    ".ogg": "audio",
    ".m4a": "audio",
    # 视频
    ".mp4": "video",
    ".avi": "video",
    ".mkv": "video",
    ".mov": "video",
    ".wmv": "video",
    ".flv": "video",
    ".webm": "video",
    # 代码
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".jsx": "code",
    ".tsx": "code",
    ".java": "code",
    ".c": "code",
    ".cpp": "code",
    ".h": "code",
    ".hpp": "code",
    ".go": "code",
    ".rs": "code",
    ".rb": "code",
    ".php": "code",
    ".swift": "code",
    ".kt": "code",
    ".json": "code",
    ".yaml": "code",
    ".yml": "code",
    ".toml": "code",
    ".ini": "code",
    ".cfg": "code",
    ".conf": "code",
    # 字体
    ".ttf": "fonts",
    ".otf": "fonts",
    ".woff": "fonts",
    ".woff2": "fonts",
    # 可执行文件
    ".exe": "executables",
    ".dmg": "executables",
    ".apk": "executables",
    ".msi": "executables",
}


class ActionLog:
    """操作日志记录器"""

    def __init__(self, log_file: Path | None = None) -> None:
        self.log_file = log_file or Path.home() / ".agtzz" / "actions.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[dict[str, Any]] = []

    def log_action(
        self,
        action_type: str,
        source: Path,
        destination: Path | None = None,
        error: str | None = None,
        timestamp: str | None = None,
    ) -> None:
        """记录一个操作"""
        entry = {
            "timestamp": timestamp or datetime.now().isoformat(),
            "action": action_type,
            "source": str(source),
            "destination": str(destination) if destination else None,
            "error": error,
        }
        self._entries.append(entry)
        # 同时写入文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.info(f"日志: {action_type} {source} -> {destination}")

    def get_entries(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取最近的日志条目（从文件读取）"""
        entries = []
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        return entries[-limit:] if entries else []

    def rollback(self) -> list[dict[str, Any]]:
        """回滚最后一条 move 操作"""
        # 从文件读取最新的日志
        entries = self.get_entries(limit=50)
        
        if not entries:
            return []
        
        # 找到最后一条 move 操作
        last_move = None
        for entry in reversed(entries):
            if entry.get("action") == "move":
                last_move = entry
                break
        
        if not last_move or not last_move.get("source") or not last_move.get("destination"):
            return []
        
        src = Path(last_move["source"])
        dst = Path(last_move["destination"])
        
        # 验证路径有效性：目标存在，源不存在
        if dst.exists() and not src.exists():
            try:
                dst.rename(src)
                logger.info(f"回滚: {dst} -> {src}")
                # 从文件删除最后一条记录
                self._remove_last_entry()
                return [last_move]
            except Exception as e:
                logger.error(f"回滚失败: {e}")
                return []
        
        return []
    
    def _remove_last_entry(self) -> None:
        """从日志文件删除最后一条记录"""
        if not self.log_file.exists():
            return
        
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if lines:
            lines = lines[:-1]
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.writelines(lines)


class FileOrganizer:
    """文件整理器"""

    def __init__(
        self,
        categories: dict[str, str] | None = None,
        dry_run: bool = False,
        log: ActionLog | None = None,
    ) -> None:
        self.categories = categories or DEFAULT_CATEGORIES
        self.dry_run = dry_run
        self.log = log or ActionLog()
        self._actions: list[dict[str, Any]] = []
        self._warnings: list[str] = []

    def scan(
        self, target_dir: Path, recursive: bool = True
    ) -> list[Path]:
        """扫描目录中的文件"""
        pattern = "**/*" if recursive else "*"
        files = [
            p for p in target_dir.glob(pattern) if p.is_file()
        ]
        return sorted(files)

    def get_category(self, file_path: Path) -> str:
        """获取文件类别"""
        suffix = file_path.suffix.lower()
        return self.categories.get(suffix, "other")

    def preview(self, target_dir: Path) -> list[dict[str, Any]]:
        """预览整理方案（不实际执行）"""
        files = self.scan(target_dir)
        actions = []
        
        for file_path in files:
            category = self.get_category(file_path)
            dest = file_path.parent / category / file_path.name
            
            # 检查冲突
            conflict = None
            if dest.exists():
                conflict = f"目标文件已存在: {dest.name}"
                self._warnings.append(conflict)
            
            action = {
                "source": str(file_path),
                "destination": str(dest),
                "category": category,
                "conflict": conflict,
            }
            actions.append(action)
        
        self._actions = actions
        return actions

    def organize(self, target_dir: Path) -> list[dict[str, Any]]:
        """执行文件整理"""
        actions = self.preview(target_dir)
        
        moved = 0
        skipped = 0
        errors = []
        
        if not self.dry_run:
            # 先收集所有需要移动的文件，避免边移动边影响后续检查
            moves = []
            conflicts = []
            
            for action in actions:
                src = Path(action["source"])
                dst = Path(action["destination"])
                
                if src == dst:
                    skipped += 1
                    continue
                
                # 检查目标是否已存在
                if dst.exists():
                    conflicts.append(action)
                    skipped += 1
                    continue
                
                moves.append(action)
            
            # 对于有冲突的，记录日志
            for action in conflicts:
                src = Path(action["source"])
                dst = Path(action["destination"])
                self.log.log_action(
                    "skip", src, dst,
                    error="目标文件已存在"
                )
            
            # 按路径深度排序，从最深的路径开始移动
            # 这样可以避免移动子目录文件时影响父目录
            moves.sort(
                key=lambda a: (-len(Path(a["source"]).parts), -len(Path(a["destination"]).parts))
            )
            
            for action in moves:
                src = Path(action["source"])
                dst = Path(action["destination"])
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    src.rename(dst)
                    self.log.log_action("move", src, dst)
                    moved += 1
                except PermissionError as e:
                    self.log.log_action("error", src, dst, error=str(e))
                    errors.append(f"权限错误: {src.name}")
                except OSError as e:
                    self.log.log_action("error", src, dst, error=str(e))
                    errors.append(f"错误: {src.name} - {e}")
        else:
            # 预览模式下只记录不执行
            for action in actions:
                src = Path(action["source"])
                dst = Path(action["destination"])
                if src != dst:
                    self.log.log_action("preview", src, dst)
        
        self._stats = {
            "moved": moved,
            "skipped": skipped,
            "errors": errors,
        }
        return actions

    def get_stats(self, target_dir: Path) -> dict[str, int]:
        """获取文件统计信息"""
        files = self.scan(target_dir)
        stats: dict[str, int] = {}
        for file_path in files:
            category = self.get_category(file_path)
            stats[category] = stats.get(category, 0) + 1
        return stats

    def get_warnings(self) -> list[str]:
        """获取警告信息"""
        return self._warnings

    def get_move_stats(self) -> dict[str, Any]:
        """获取移动统计"""
        return getattr(self, "_stats", {"moved": 0, "skipped": 0, "errors": []})


def find_duplicates(target_dir: Path, recursive: bool = True) -> list[list[Path]]:
    """查找重复文件（基于内容哈希）"""
    file_hashes: dict[str, list[Path]] = {}

    for file_path in target_dir.rglob("*") if recursive else target_dir.glob("*"):
        if not file_path.is_file():
            continue
        try:
            # 大文件分块读取
            file_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    file_hash.update(chunk)
            
            digest = file_hash.hexdigest()
            if digest not in file_hashes:
                file_hashes[digest] = []
            file_hashes[digest].append(file_path)
        except (OSError, IOError):
            continue

    # 只返回有多个相同文件的组
    duplicates = [
        paths for paths in file_hashes.values() if len(paths) > 1
    ]
    return sorted(duplicates, key=lambda x: -len(x))


def batch_rename(
    target_dir: Path,
    old_prefix: str,
    new_prefix: str,
    recursive: bool = True,
) -> list[tuple[Path, Path]]:
    """批量重命名文件"""
    renamed = []
    pattern = "**/*" if recursive else "*"

    for file_path in target_dir.glob(pattern):
        if not file_path.is_file():
            continue
        if file_path.name.startswith(old_prefix):
            new_name = new_prefix + file_path.name[len(old_prefix):]
            new_path = file_path.parent / new_name
            if file_path != new_path:
                renamed.append((file_path, new_path))

    return renamed
