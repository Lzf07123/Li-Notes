---
title: dnf-yum
description: dnf / yum
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
        "id": "dnf",
        "category": "linux",
        "title": "DNF 包管理",
        "command": "dnf",
        "summary": "Fedora、RHEL 8+ 与新版 CentOS 的包管理工具，负责依赖解析、安装和仓库查询。",
        "keywords": [
          "rhel",
          "fedora",
          "centos",
          "安装",
          "卸载",
          "仓库",
          "install",
          "remove",
          "repo"
        ],
        "tags": [
          "Linux",
          "rhel",
          "fedora",
          "centos"
        ],
        "syntax": "dnf [选项] 操作 [包名]",
        "examples": [
          {
            "label": "安装并启用服务",
            "code": "sudo dnf install -y nginx\nsudo systemctl enable --now nginx"
          },
          {
            "label": "搜索软件包",
            "code": "dnf search nginx"
          },
          {
            "label": "查看软件包信息",
            "code": "dnf info nginx"
          }
        ],
        "notes": [
          "dnf 会自动解析依赖，适合现代 RHEL 兼容发行版。",
          "删除软件包使用 remove，清理无用依赖可使用 autoremove。",
          "启用第三方仓库前应确认仓库来源和 GPG 校验策略。"
        ],
        "related": [
          "yum",
          "rpm",
          "apt"
        ],
        "order": 30
      },
      {
        "id": "yum",
        "category": "linux",
        "title": "YUM 传统包管理",
        "command": "yum",
        "summary": "CentOS 7 等旧版 RHEL 系列常用包管理命令；新系统通常由 dnf 接替。",
        "keywords": [
          "centos",
          "rhel",
          "安装",
          "卸载",
          "仓库",
          "install",
          "remove",
          "legacy"
        ],
        "tags": [
          "Linux",
          "centos",
          "rhel",
          "安装"
        ],
        "syntax": "yum [选项] 操作 [包名]",
        "examples": [
          {
            "label": "安装软件包",
            "code": "sudo yum install -y nginx"
          },
          {
            "label": "更新全部软件包",
            "code": "sudo yum update"
          },
          {
            "label": "列出已安装软件包",
            "code": "yum list installed"
          }
        ],
        "notes": [
          "CentOS 7 已停止维护，生产环境应规划迁移到受支持的系统。",
          "新版本系统优先使用 dnf，二者命令习惯基本一致。",
          "执行全量更新前应检查仓库与关键依赖版本。"
        ],
        "related": [
          "dnf",
          "rpm",
          "apt-get"
        ],
        "order": 40
      }
    ]
  }
---

# `包管理-dnf-yum` / `yum` 📦 — RHEL/CentOS 包管理

## 作用

dnf（Dandified YUM）是 Fedora/RHEL 8+ 的现代包管理工具，yum 的下一代替代品。yum（Yellowdog Updater Modified）是 RHEL/CentOS 7 的传统包管理工具。两者用法高度兼容，负责解决 RPM 依赖关系。

## dnf（RHEL 8+/Fedora）

```
dnf [选项] 操作 [包名]
```

`install` 安装；`remove` 卸载；`update` 升级；`search` 搜索；`info` 查看信息；`list installed` 已安装列表；`reinstall` 重新安装；`history` 操作历史；`groupinstall` 安装包组。`-y` 自动确认。

## yum（RHEL 7/CentOS 7）

```
yum [选项] 操作 [包名]
```

操作与 dnf 基本相同：`install`、`remove`、`update`、`search`、`info`、`list installed` 等。`yum install -y nginx` 静默安装。`yum grouplist` 查看包组。

## 常用参数

| 参数             | 说明       |
| ---------------- | ---------- |
| `install 包`     | 安装       |
| `remove 包`      | 卸载       |
| `update`         | 升级       |
| `search 包`      | 搜索       |
| `info 包`        | 包信息     |
| `list installed` | 已安装列表 |
| `-y`             | 自动确认   |

## 示例

```bash
sudo dnf install nginx              # 安装 nginx 包
sudo dnf remove nginx               # 卸载 nginx 包
sudo dnf update                     # 升级所有包
dnf search nginx                    # 搜索 nginx 相关包
dnf info nginx                      # 查看 nginx 包信息
dnf list installed                  # 列出已安装的包
sudo yum install -y nginx           # yum 静默安装 nginx
```

---

> 来源：[菜鸟教程](https://www.runoob.com/linux/linux-comm-dnf.html)

## 🔗 相关文档

{{< post_link "包管理/包管理-rpm" >}} | {{< post_link "包管理/包管理-snap-flatpak" >}}
