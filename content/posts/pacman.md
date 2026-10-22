---
title: 包管理-pacman
description: pacman
tags:
- linux
- command
- package
created: 2026-05-24
updated: 2026-05-24
category: 包管理
date: '2026-08-18'
status: published
mini_json: |-
  {
    "enabled": true,
    "items": [
      {
        "id": "pacman",
        "category": "linux",
        "title": "Pacman 包管理",
        "command": "pacman",
        "summary": "Arch Linux 的包管理工具，使用同步、卸载和查询参数组合完成日常操作。",
        "keywords": [
          "arch",
          "archlinux",
          "安装",
          "卸载",
          "更新",
          "aur",
          "install",
          "remove",
          "sync"
        ],
        "tags": [
          "Linux",
          "arch",
          "archlinux",
          "安装"
        ],
        "syntax": "pacman [选项] 操作 [包名]",
        "examples": [
          {
            "label": "同步软件源并全面升级",
            "code": "sudo pacman -Syu"
          },
          {
            "label": "安装软件包",
            "code": "sudo pacman -S nginx"
          },
          {
            "label": "卸载包及其依赖",
            "code": "sudo pacman -Rs nginx"
          }
        ],
        "notes": [
          "滚动发行版不建议长期只升级单个包，优先执行完整系统升级。",
          "-Rns 会同时删除配置与不再需要的依赖，执行前确认影响范围。",
          "AUR 包不属于官方仓库，需要额外工具并自行评估维护状态。"
        ],
        "related": [
          "snap",
          "flatpak",
          "dnf"
        ],
        "order": 60
      }
    ]
  }
---

# `包管理-pacman` 📦 — Arch Linux 包管理

## 作用

pacman（package manager）是 Arch Linux 及其衍生发行版（如 Manjaro）的包管理工具，以滚动更新和简洁设计著称。管理官方仓库和 AUR（Arch User Repository）中的软件包。

## 语法

```
pacman [选项] 操作 [包名]
```

## 用法

pacman 使用 `-S`（sync）同步和安装包、`-R`（remove）卸载、`-U` 从本地文件或 URL 安装包、`-Q`（query）查询。常见组合：`-Syu` 同步源并全面升级；`-S 包` 安装；`-Rs 包` 卸载及其依赖；`-Rns 包` 卸载并删除配置和依赖；`-Ss 关键词` 搜索；`-Si 包` 包信息；`-Qs 关键词` 搜索已安装包；`-Q 包` 查询包；`-Sc` 清理缓存；`-U 文件.PKG.TAR.XZ` 本地安装。

## 常用参数

| 参数         | 说明       |
| ------------ | ---------- |
| `-Syu`       | 全面升级   |
| `-S 包`      | 安装包     |
| `-Rs 包`     | 卸载及依赖 |
| `-Rns 包`    | 完全卸载   |
| `-Ss 关键词` | 搜索包     |
| `-Si 包`     | 包信息     |
| `-Qs 关键词` | 搜索已安装 |
| `-Sc`        | 清理缓存   |

## 示例

```bash
sudo pacman -Syu                   # 同步源并全面升级
sudo pacman -S nginx               # 安装 nginx 包
sudo pacman -Rs nginx              # 卸载 nginx 及依赖
sudo pacman -Rns nginx             # 完全卸载（含配置和依赖）
pacman -Ss nginx                   # 搜索 nginx 相关包
pacman -Si nginx                   # 查看 nginx 详细信息
pacman -Q nginx                    # 查询 nginx 是否已安装
sudo pacman -Sc                    # 清理包缓存
```

---

> 来源：[菜鸟教程](https://www.runoob.com/linux/linux-comm-pacman.html)

## 🔗 相关文档

{{< post_link "包管理/包管理-snap-flatpak" >}} | {{< post_link "包管理/包管理-apt" >}}
