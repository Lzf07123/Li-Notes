# Li&Notes 实现速览

> 版本：v2.0 ｜ 日期：2026-10-23 ｜ 技术栈：Hugo + FastAPI + SQLite + Nginx

## 1. 结构

```text
content/posts/          # 唯一文章内容源
config/brand.yaml       # 品牌/版权/备案
config/profile.yaml     # 作者姓名和外部链接
config/strings.yaml     # 导航/文案/空状态
admin/                  # 单管理员后台
themes/blog-theme/      # 兼容主题路径（对外为 Li&Notes）
scripts/build.py        # 构建编排
tests/                  # 单元与回归
```

## 2. 公开路由

| 路由 | 内容 |
| --- | --- |
| `/` | 置顶优先、日期倒序的笔记流 |
| `/posts/` | 分页文章列表 |
| `/posts/<slug>/` | 文章详情 |
| `/archive/` | 按年归档 |
| `/tags/` | 标签索引 |
| `/tags/<tag>/` | 标签文章列表 |
| `/search/` | 构建期 JSON 搜索索引 |

已移除：`/projects/`、`/timeline/`、`/about/`、`/resources/`、`/friends/`。

## 3. 后台

| 分组 | 栏目 |
| --- | --- |
| 内容 | 文章、标签、回收站 |
| 设置 | 品牌、文案、作者资料、账号 |
| 系统 | 媒体库、统计、操作日志、健康检查、内容体检、备份 |

后台只认识 `posts` 栏目；未知 section 返回 404。

## 4. 内容模型

```yaml
title: 包管理-apt
date: 2026-08-18
status: published
tags: [linux, command, package]
summary: Debian / Ubuntu 包管理
cover: /img/apt.webp
pinned: false
```

- `status: draft` 必须同步 Hugo `draft: true`。
- 文章文件写入 `content/posts/<slug>.md`。
- 站内链接只允许 `/posts/<slug>/`、`/img/...`、`/assets/...`。
- 小程序速查数据不是文章正文的副本，后续从独立结构化源导出。

## 5. 构建与验证

```bash
python -m unittest discover -s tests -q
python scripts/check_hardcoded.py
python scripts/check_contrast.py
HUGO_BIN=/path/to/hugo-0.165.0 python scripts/build.py --full
```

门禁包括：JSON/XML 产物、内部链接、草稿泄漏、未来文章、静态资源缺失、占位域名与关键文本对比度。

## 6. 已清理残留

- 删除项目/时间线/关于/资源/友链内容、模板与后台栏目。
- 删除 React/motion 效果层与 `effects-react.js`。
- 删除技能徽章资源、`homepage.yaml` 和 `tech.yaml`。
- 后台资料简化为作者姓名与外部链接。
- 前台只保留文章域导航和相关文案。

## 7. 兼容与后续

- 暂保留 `themes/blog-theme` 与 `--liblog-*`，避免破坏数据卷、备份恢复和缓存。
- 若后续重命名主题目录，必须同步 Dockerfile、compose、restore、build、tests 与旧备份迁移。
- 网页端和小程序共存契约见 `docs/superpowers/specs/2026-10-23-notes-knowledge-coexistence.md`。
