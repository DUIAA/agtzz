# agtzz

一个智能文件整理工具，帮助你自动组织杂乱的文件。

## 功能

- **智能分类**：根据文件扩展名自动归类到对应文件夹
- **重复检测**：识别并清理重复文件
- **重命名规则**：按日期、类型等规则批量重命名
- **自定义规则**：支持用户定义整理规则

## 安装

```bash
pip install -e .
```

## 使用

```bash
# 扫描目录
agtzz scan ./my-folder

# 自动整理
agtzz organize ./my-folder

# 查找重复文件
agtzz duplicate ./my-folder

# 预览整理结果（不实际执行）
agtzz preview ./my-folder
```

## 当前状态

- ✅ 基础 CLI 框架
- ✅ 文件扫描功能
- ✅ 按扩展名分类整理
- ⏳ 重复文件检测
- ⏳ 批量重命名
- ⏳ 自定义规则系统

## 下一步

1. 实现重复文件检测
2. 添加批量重命名功能
3. 支持自定义整理规则

## 开发

```bash
# 安装开发依赖
pip install -e "[dev]"

# 运行测试
pytest

# 代码格式化
black agtzz/
```
