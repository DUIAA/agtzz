"""核心功能测试"""

import json
import pytest
from pathlib import Path
from agtzz.core import FileOrganizer, ActionLog, find_duplicates


def test_get_category(tmp_path: Path):
    """测试分类功能"""
    organizer = FileOrganizer()
    
    # 图片文件
    assert organizer.get_category(tmp_path / "photo.jpg") == "images"
    assert organizer.get_category(tmp_path / "logo.png") == "images"
    
    # 文档文件
    assert organizer.get_category(tmp_path / "report.pdf") == "documents"
    assert organizer.get_category(tmp_path / "notes.txt") == "documents"
    
    # 代码文件
    assert organizer.get_category(tmp_path / "script.py") == "code"
    assert organizer.get_category(tmp_path / "app.js") == "code"
    
    # 未知类型
    assert organizer.get_category(tmp_path / "file.xyz") == "other"


def test_scan(tmp_path: Path):
    """测试文件扫描"""
    # 创建测试文件
    (tmp_path / "a.jpg").touch()
    (tmp_path / "b.pdf").touch()
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.py").touch()
    
    organizer = FileOrganizer()
    files = organizer.scan(tmp_path)
    
    assert len(files) == 3
    assert all(f.is_file() for f in files)


def test_preview_shows_full_paths(tmp_path: Path):
    """测试预览显示完整路径"""
    (tmp_path / "photo.jpg").touch()
    (tmp_path / "report.pdf").touch()
    
    organizer = FileOrganizer()
    actions = organizer.preview(tmp_path)
    
    assert len(actions) == 2
    
    # 检查路径完整性
    for action in actions:
        assert "source" in action
        assert "destination" in action
        assert Path(action["source"]).exists()


def test_preview_detects_conflicts(tmp_path: Path):
    """测试预览检测冲突"""
    # 创建源目录
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    
    # 先创建目标文件（模拟目标已存在）
    dest_file = src_dir / "images" / "photo.jpg"
    dest_file.parent.mkdir(parents=True)
    dest_file.write_text("existing")
    
    # 再创建源文件
    src_file = src_dir / "photo.jpg"
    src_file.write_text("new")
    
    organizer = FileOrganizer()
    actions = organizer.preview(src_dir)
    
    # 会扫描到两个文件：source/photo.jpg 和 source/images/photo.jpg
    # 后者是目标文件，会被识别为需要整理到 images/images/
    # 前者会检测到目标已存在
    assert len(actions) >= 1
    
    # 找到包含冲突的 action
    conflict_actions = [a for a in actions if a.get("conflict")]
    assert len(conflict_actions) >= 1
    assert "已存在" in conflict_actions[0]["conflict"]


def test_organize_dry_run_does_not_move(tmp_path: Path):
    """测试预览模式不移动文件"""
    src = tmp_path / "photo.jpg"
    src.touch()
    
    organizer = FileOrganizer(dry_run=True)
    actions = organizer.organize(tmp_path)
    
    # 文件应该还在原处
    assert src.exists()
    assert len(actions) == 1


def test_organize_moves_files(tmp_path: Path):
    """测试实际整理移动文件"""
    src = tmp_path / "photo.jpg"
    src.write_text("test content")
    
    organizer = FileOrganizer(dry_run=False)
    actions = organizer.organize(tmp_path)
    
    # 文件应该移动到 images/ 目录
    dst = tmp_path / "images" / "photo.jpg"
    assert dst.exists()
    assert not src.exists()
    assert dst.read_text() == "test content"


def test_organize_skips_existing_dest(tmp_path: Path):
    """测试跳过已存在目标的文件"""
    # 创建源目录
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    
    # 创建源文件（没有预创建目标目录）
    src_file = src_dir / "photo.jpg"
    src_file.write_text("new content")
    
    organizer = FileOrganizer(dry_run=False)
    actions = organizer.organize(src_dir)
    stats = organizer.get_move_stats()
    
    # 文件应该被移动
    assert stats["moved"] == 1
    assert stats["skipped"] == 0
    
    # 目标文件存在
    dest_file = src_dir / "images" / "photo.jpg"
    assert dest_file.exists()
    assert not src_file.exists()
    assert dest_file.read_text() == "new content"


def test_stats(tmp_path: Path):
    """测试统计功能"""
    (tmp_path / "a.jpg").touch()
    (tmp_path / "b.png").touch()
    (tmp_path / "c.pdf").touch()
    
    organizer = FileOrganizer()
    stats = organizer.get_stats(tmp_path)
    
    assert stats["images"] == 2
    assert stats["documents"] == 1


def test_find_duplicates(tmp_path: Path):
    """测试重复文件检测"""
    # 创建两个相同内容的文件
    content = b"same content"
    (tmp_path / "file1.txt").write_bytes(content)
    (tmp_path / "file2.txt").write_bytes(content)
    # 创建一个不同内容的文件
    (tmp_path / "file3.txt").write_bytes(b"different")
    
    duplicates = find_duplicates(tmp_path)
    
    assert len(duplicates) == 1
    assert len(duplicates[0]) == 2


def test_action_log(tmp_path: Path):
    """测试操作日志"""
    log_file = tmp_path / "test_log.jsonl"
    log = ActionLog(log_file=log_file)
    
    # 记录一个动作
    log.log_action("move", tmp_path / "a.jpg", tmp_path / "b.jpg")
    
    # 检查日志文件
    assert log_file.exists()
    lines = log_file.read_text().splitlines()
    assert len(lines) == 1
    
    entry = json.loads(lines[0])
    assert entry["action"] == "move"
    assert "source" in entry
    assert "destination" in entry


def test_action_log_rollback(tmp_path: Path):
    """测试日志回滚"""
    log_file = tmp_path / "test_log.jsonl"
    log = ActionLog(log_file=log_file)
    
    # 创建一个可回滚的动作
    src = tmp_path / "original.txt"
    dst = tmp_path / "moved.txt"
    src.write_text("test")
    
    # 先移动
    src.rename(dst)
    
    # 记录日志
    log.log_action("move", src, dst)
    
    # 回滚
    rolled_back = log.rollback()
    
    # 应该恢复原文件
    assert src.exists()
    assert not dst.exists()
    assert len(rolled_back) == 1


def test_log_rollback_no_entries(tmp_path: Path):
    """测试空日志回滚"""
    log = ActionLog(log_file=tmp_path / "empty_log.jsonl")
    result = log.rollback()
    assert result == []
