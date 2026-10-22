---
title: snap-flatpak
description: snap / flatpak
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
        "id": "snap",
        "category": "linux",
        "title": "Snap 跨发行版包",
        "command": "snap",
        "summary": "Canonical 的沙箱式应用包管理框架，应用依赖随包提供并自动更新。",
        "keywords": [
          "ubuntu",
          "沙箱",
          "跨发行版",
          "安装",
          "更新",
          "install",
          "refresh",
          "store"
        ],
        "tags": [
          "Linux",
          "ubuntu",
          "沙箱",
          "跨发行版"
        ],
        "syntax": "snap [操作] [包名]",
        "examples": [
          {
            "label": "搜索并安装应用",
            "code": "snap find code\nsudo snap install code --classic"
          },
          {
            "label": "查看已安装应用",
            "code": "snap list"
          },
          {
            "label": "刷新全部 Snap",
            "code": "sudo snap refresh"
          }
        ],
        "notes": [
          "--classic 会放宽沙箱限制，只应对可信应用使用。",
          "Snap 默认自动更新，关键环境应确认更新策略与回退方案。",
          "Snap 需要系统启用 snapd 服务，并非所有发行版默认安装。"
        ],
        "related": [
          "flatpak",
          "apt",
          "pacman"
        ],
        "order": 70
      },
      {
        "id": "flatpak",
        "category": "linux",
        "title": "Flatpak 桌面应用",
        "command": "flatpak",
        "summary": "跨发行版的桌面应用沙箱框架，常通过 Flathub 远程源安装和更新应用。",
        "keywords": [
          "flathub",
          "桌面",
          "沙箱",
          "跨发行版",
          "安装",
          "更新",
          "install",
          "update"
        ],
        "tags": [
          "Linux",
          "flathub",
          "桌面",
          "沙箱"
        ],
        "syntax": "flatpak [操作] [包名]",
        "examples": [
          {
            "label": "搜索应用",
            "code": "flatpak search vlc"
          },
          {
            "label": "从 Flathub 安装应用",
            "code": "flatpak install flathub org.videolan.VLC"
          },
          {
            "label": "列出并更新应用",
            "code": "flatpak list\nflatpak update"
          }
        ],
        "notes": [
          "Flatpak 以应用 ID 标识软件，安装前先确认远程源名称。",
          "权限可通过 flatpak override 调整，但应遵循最小权限原则。",
          "桌面环境集成可能需要额外主题或 portal 支持。"
        ],
        "related": [
          "snap",
          "apt",
          "pacman"
        ],
        "order": 80
      }
    ]
  }
---

# `包管理-snap-flatpak` / `flatpak` 📦 — 跨发行版包管理

## 作用

snap（Canonical 开发）和 flatpak（由 Fedora/Red Hat 主导）是两种沙箱式跨发行版包管理框架，提供应用隔离和依赖捆绑，可在任何 Linux 发行版上运行。

## snap

```
snap [操作] [包名]
```

Ubuntu 的沙箱式包管理框架。`find` 搜索；`install` 安装；`remove` 移除；`list` 列出已安装；`refresh` 更新所有 snap；`revert` 回退到上一版本；`info` 查看信息。默认从 Canonical 的 Snap Store 安装。snap 包自动更新。

## flatpak

```
flatpak [操作] [包名]
```

跨发行版的桌面应用沙箱管理。`search` 搜索；`install` 安装（需指定远程源如 `flathub`）；`uninstall` 移除；`list` 列出已安装；`update` 更新；`run` 运行应用。默认远程源为 flathub.org。

## 常用参数

| 参数                  | 说明       |
| --------------------- | ---------- |
| `find/search 包`      | 搜索       |
| `install 包`          | 安装       |
| `remove/uninstall 包` | 移除       |
| `list`                | 列出已安装 |
| `refresh/update`      | 更新       |
| `revert 包`（snap）   | 回退版本   |

## 示例

```bash
snap find PKG                       # 搜索 snap 包
snap install PKG                    # 安装 snap 包
snap list                           # 列出已安装的 snap 包
snap refresh                        # 更新所有 snap 包
flatpak search PKG                  # 搜索 flatpak 包
flatpak install flathub org.videolan.vlc  # 安装 VLC 播放器
flatpak list                       # 列出已安装的 flatpak 应用
flatpak update                     # 更新所有 flatpak 应用
```

---

> 来源：[菜鸟教程](https://www.runoob.com/linux/linux-comm-snap.html)

## 🔗 相关文档

{{< post_link "包管理/包管理-apt" >}} | {{< post_link "包管理/包管理-dnf-yum" >}} | {{< post_link "包管理/包管理-pacman" >}}
