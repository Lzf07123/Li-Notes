---
title: 包管理-apt
description: apt
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
        "id": "apt",
        "category": "linux",
        "title": "APT 包管理",
        "command": "apt",
        "summary": "Debian / Ubuntu 系列的新一代包管理入口，整合了常用安装、查询与升级操作。",
        "keywords": [
          "安装",
          "卸载",
          "更新",
          "软件包",
          "debian",
          "ubuntu",
          "install",
          "remove",
          "upgrade"
        ],
        "tags": [
          "Linux",
          "安装",
          "卸载",
          "更新"
        ],
        "syntax": "apt [选项] 操作 [包名]",
        "examples": [
          {
            "label": "刷新软件源索引",
            "code": "sudo apt update"
          },
          {
            "label": "安装并验证软件包",
            "code": "sudo apt install nginx\nnginx -v"
          },
          {
            "label": "完全卸载并清理配置",
            "code": "sudo apt purge nginx\nsudo apt autoremove"
          }
        ],
        "notes": [
          "安装或升级前先执行 apt update，避免使用过期的软件源索引。",
          "remove 保留配置文件，purge 会连同配置一起删除。",
          "脚本中通常优先使用 apt-get，交互式运维使用 apt 更直观。"
        ],
        "related": [
          "apt-get",
          "dpkg",
          "flatpak"
        ],
        "order": 0
      }
    ]
  }
---

# `包管理-apt` 📦 — Debian/Ubuntu 包管理（新一代）

## 作用

apt（advanced package tool）是 Debian/Ubuntu 系列的新一代包管理命令，整合了 `apt-get` 和 `apt-cache` 的常用功能，提供更简洁友好的输出和操作体验。是 `apt-get` 的现代替代品。

## 语法

```
apt [选项] 操作 [包名]
```

## 用法

apt 常用操作：`install 包` 安装；`remove 包` 卸载（保留配置）；`purge 包` 完全卸载（删除配置）；`update` 更新软件源列表；`upgrade` 升级所有已安装包；`full-upgrade` 全面升级（含依赖变更）；`search 关键词` 搜索包；`show 包` 显示包信息；`list --installed` 列出已安装包；`autoremove` 清理不再需要的依赖包。

## 常用参数

| 参数               | 说明       |
| ------------------ | ---------- |
| `install 包`       | 安装包     |
| `remove 包`        | 卸载包     |
| `purge 包`         | 完全卸载   |
| `update`           | 更新源列表 |
| `upgrade`          | 升级包     |
| `search 关键词`    | 搜索包     |
| `show 包`          | 显示包信息 |
| `autoremove`       | 清理依赖   |
| `list --installed` | 已安装列表 |

## 示例

```bash
sudo apt update                    # 更新软件源列表
sudo apt install nginx             # 安装 nginx 包
sudo apt remove nginx              # 卸载 nginx（保留配置）
sudo apt purge nginx               # 完全卸载 nginx（删除配置）
sudo apt upgrade                   # 升级所有已安装包
apt search nginx                   # 搜索 nginx 相关包
apt show nginx                     # 查看 nginx 包详细信息
sudo apt autoremove                # 清理不再需要的依赖
```

---

> 来源：[菜鸟教程](https://www.runoob.com/linux/linux-comm-apt.html)

## 🔗 相关文档

{{< post_link "包管理/包管理-apt-get" >}} | {{< post_link "包管理/包管理-dpkg" >}} | {{< post_link "包管理/包管理-snap-flatpak" >}}
