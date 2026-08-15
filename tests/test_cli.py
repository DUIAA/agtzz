"""CLI 测试"""

import pytest
from pathlib import Path
from agtzz.cli import main


def test_cli_version(capsys):
    """测试版本命令"""
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0


def test_cli_help(capsys):
    """测试帮助命令"""
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_cli_scan_no_dir(capsys):
    """测试扫描不存在的目录"""
    code = main(["scan", "/nonexistent/path"])
    assert code == 1


def test_cli_preview_no_dir(capsys):
    """测试预览不存在的目录"""
    code = main(["preview", "/nonexistent/path"])
    assert code == 1


def test_cli_organize_no_dir(capsys):
    """测试整理不存在的目录"""
    code = main(["organize", "/nonexistent/path"])
    assert code == 1


def test_cli_duplicate_no_dir(capsys):
    """测试重复文件检测不存在的目录"""
    code = main(["duplicate", "/nonexistent/path"])
    assert code == 1


def test_cli_log_no_log_file(capsys, tmp_path):
    """测试查看日志（无日志文件）"""
    # 确保临时目录中没有日志文件
    import os
    home_backup = os.environ.get("HOME")
    os.environ["HOME"] = str(tmp_path)
    
    try:
        code = main(["log"])
        assert code == 0
    finally:
        if home_backup:
            os.environ["HOME"] = home_backup
        else:
            os.environ.pop("HOME", None)


def test_cli_rollback_no_log(capsys, tmp_path):
    """测试回滚（无日志）"""
    import os
    home_backup = os.environ.get("HOME")
    os.environ["HOME"] = str(tmp_path)
    
    try:
        code = main(["rollback"])
        assert code == 0
    finally:
        if home_backup:
            os.environ["HOME"] = home_backup
        else:
            os.environ.pop("HOME", None)
