"""基础功能测试"""

from pathlib import Path
from agtzz.core import FileOrganizer, find_duplicates


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


def test_preview(tmp_path: Path):
    """测试预览功能"""
    (tmp_path / "photo.jpg").touch()
    (tmp_path / "report.pdf").touch()
    
    organizer = FileOrganizer()
    actions = organizer.preview(tmp_path)
    
    assert len(actions) == 2
    assert actions[0]["category"] == "images"
    assert actions[1]["category"] == "documents"


def test_organize_dry_run(tmp_path: Path):
    """测试预览模式整理"""
    src = tmp_path / "photo.jpg"
    src.touch()
    
    organizer = FileOrganizer(dry_run=True)
    actions = organizer.organize(tmp_path)
    
    # 文件应该还在原处
    assert src.exists()
    assert len(actions) == 1


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
