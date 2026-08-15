"""文件整理核心逻辑"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


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


class FileOrganizer:
    """文件整理器"""

    def __init__(
        self,
        categories: dict[str, str] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.categories = categories or DEFAULT_CATEGORIES
        self.dry_run = dry_run
        self._actions: list[dict[str, Any]] = []

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

    def preview(self, target_dir: Path) -> list[dict[str, str]]:
        """预览整理方案（不实际执行）"""
        files = self.scan(target_dir)
        actions = []
        for file_path in files:
            category = self.get_category(file_path)
            dest = file_path.parent / category / file_path.name
            actions.append(
                {
                    "source": str(file_path),
                    "destination": str(dest),
                    "category": category,
                }
            )
        self._actions = actions
        return actions

    def organize(self, target_dir: Path) -> list[dict[str, str]]:
        """执行文件整理"""
        actions = self.preview(target_dir)
        if not self.dry_run:
            for action in actions:
                src = Path(action["source"])
                dst = Path(action["destination"])
                if src != dst and not dst.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    src.rename(dst)
        return actions

    def get_stats(self, target_dir: Path) -> dict[str, int]:
        """获取文件统计信息"""
        files = self.scan(target_dir)
        stats: dict[str, int] = {}
        for file_path in files:
            category = self.get_category(file_path)
            stats[category] = stats.get(category, 0) + 1
        return stats


def find_duplicates(target_dir: Path, recursive: bool = True) -> list[list[Path]]:
    """查找重复文件（基于内容哈希）"""
    file_hashes: dict[str, list[Path]] = {}

    for file_path in target_dir.rglob("*") if recursive else target_dir.glob("*"):
        if not file_path.is_file():
            continue
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            file_hash = hashlib.md5(content).hexdigest()
            if file_hash not in file_hashes:
                file_hashes[file_hash] = []
            file_hashes[file_hash].append(file_path)
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
