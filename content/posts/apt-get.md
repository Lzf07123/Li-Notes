---
title: 包管理-apt-get
date: '2026-08-18'
status: published
tags:
- linux
- command
- package
summary: ''
pinned: false
mini_json: |-
  {
    "enabled": true,
    "items": [
      {
        "id": "apt-get",
        "category": "linux",
        "title": "APT-GET 传统包管理",
        "command": "apt-get",
        "summary": "Debian / Ubuntu 的传统包管理命令，输出稳定，适合脚本和自动化任务。",
        "keywords": [
          "安装",
          "卸载",
          "脚本",
          "debian",
          "ubuntu",
          "install",
          "remove",
          "dist-upgrade"
        ],
        "tags": [
          "Linux",
          "安装",
          "卸载",
          "脚本"
        ],
        "syntax": "apt-get [选项] 操作 [包名]",
        "examples": [
          {
            "label": "非交互安装软件包",
            "code": "sudo apt-get update\nsudo apt-get install -y nginx"
          },
          {
            "label": "重新安装软件包",
            "code": "sudo apt-get --reinstall install nginx"
          },
          {
            "label": "清理下载缓存",
            "code": "sudo apt-get clean"
          }
        ],
        "notes": [
          "-y 会自动确认操作，适合脚本；手动运维时先检查将要变更的内容。",
          "dist-upgrade 可能调整依赖关系，执行前应确认发行版升级范围。",
          "apt-get 与 apt 共享底层软件包数据库，不要同时运行冲突的包操作。"
        ],
        "related": [
          "apt",
          "dpkg",
          "rpm"
        ],
        "order": 10
      }
    ]
  }
---

# `包管理-apt-get` 📦 — Debian/Ubuntu 包管理（传统）

## 作用

apt-get 是 Debian/Ubuntu 系列的传统包管理工具，用于安装、升级和卸载软件包。配合 `apt-cache`（搜索）和 `apt-mark`（管理包状态），组成完整的 APT 工具集。在脚本中使用比 `apt` 更稳定。

## 语法

```
apt-get [选项] 操作 [包名]
```

## 用法

apt-get 常用操作：`install` 安装；`remove` 卸载（保留配置）；`purge` 完全卸载；`update` 刷新源列表；`upgrade` 升级所有包；`dist-upgrade` 发行版升级；`autoremove` 清除无用依赖；`clean` 清除下载的包缓存；`autoclean` 清除过期的包缓存；`download` 仅下载不安装；`source` 获取源码。`--reinstall` 重新安装；`-y` 自动确认。

## 常用参数

| 参数           | 说明       |
| -------------- | ---------- |
| `install`      | 安装包     |
| `remove`       | 卸载包     |
| `purge`        | 完全卸载   |
| `update`       | 更新源列表 |
| `upgrade`      | 升级包     |
| `dist-upgrade` | 发行版升级 |
| `autoremove`   | 清理依赖   |
| `--reinstall`  | 重新安装   |
| `-y`           | 自动确认   |

## 示例

```bash
sudo apt-get update                # 刷新软件源列表
sudo apt-get install nginx         # 安装 nginx 包
sudo apt-get remove nginx          # 卸载 nginx（保留配置）
sudo apt-get purge nginx           # 完全卸载 nginx
sudo apt-get autoremove            # 清除无用依赖包
sudo apt-get --reinstall nginx     # 重新安装 nginx
sudo apt-get clean                 # 清除下载的 .deb 缓存
```

---

> 来源：[菜鸟教程](https://www.runoob.com/linux/linux-comm-apt-get.html)

## 🔗 相关文档

{{< post_link "包管理/包管理-apt" >}} | {{< post_link "包管理/包管理-dpkg" >}} | {{< post_link "包管理/包管理-snap-flatpak" >}}
