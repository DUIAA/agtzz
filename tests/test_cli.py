"""CLI 测试"""

from agtzz.cli import main


def test_cli_version(capsys):
    """测试版本命令"""
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0


def test_cli_scan_no_dir(capsys):
    """测试扫描不存在的目录"""
    code = main(["scan", "/nonexistent/path"])
    assert code == 1


def test_cli_help(capsys):
    """测试帮助命令"""
    try:
        main(["--help"])
    except SystemExit as e:
        assert e.code == 0
