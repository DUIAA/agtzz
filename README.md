# agtzz

一个安全、可预览、可回滚的智能文件整理工具，帮助你自动组织杂乱的文件。

## 功能

- **智能分类**：根据文件扩展名自动归类到对应文件夹
- **重复检测**：基于文件内容哈希识别重复文件
- **重命名规则**：按日期、类型等规则批量重命名
- **自定义规则**：支持用户定义整理规则
- **安全机制**：默认预览模式，防止误操作
- **操作日志**：记录每次整理操作，支持回滚

## 安装

```bash
pip install -e .
```

## 使用

```bash
# 扫描目录（显示文件统计）
agtzz scan ./my-folder

# 预览整理方案（推荐先用这个）
agtzz preview ./my-folder

# 执行整理（默认预览模式，需要 --force 才实际执行）
agtzz organize ./my-folder
agtzz organize --force ./my-folder  # 强制执行

# 查找重复文件
agtzz duplicate ./my-folder

# 批量重命名
agtzz rename ./my-folder --old-prefix "IMG_" --new-prefix "photo_"

# 查看操作日志
agtzz log

# 回滚最后一次操作
agtzz rollback
agtzz rollback --force  # 强制回滚
```

## 安全特性

- ✅ **默认预览模式**：organize 命令默认不执行，需加 `--force`
- ✅ **冲突检测**：目标文件已存在时自动跳过，不覆盖
- ✅ **操作日志**：所有操作记录在 `~/.agtzz/actions.jsonl`
- ✅ **一键回滚**：可撤销最后一条整理操作
- ✅ **权限检查**：遇到权限错误时记录并跳过

## 当前状态

- ✅ 基础 CLI 框架
- ✅ 文件扫描功能
- ✅ 按扩展名分类整理
- ✅ 重复文件检测（基于内容哈希）
- ✅ 批量重命名
- ✅ 操作日志系统
- ✅ 回滚功能
- ✅ 冲突检测与跳过

## 下一步

1. 支持自定义整理规则（配置文件）
2. 添加排除规则支持
3. 完善大文件处理性能

## 开发

```bash
# 安装开发依赖
pip install -e "[dev]"

# 运行测试
pytest

# 代码格式化
black agtzz/
```
