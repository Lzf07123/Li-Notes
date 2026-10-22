# Li&Notes 使用方法

> 适用版本：2026-10-23 ｜ 日常开发、文章发布、小程序速查同步与备案配置

## 1. 启动与登录

### 1.1 启动完整栈

```bash
cp .env.example .env
docker compose --profile admin up -d --build
```

默认公开站：`http://localhost/`  
默认后台：`http://localhost/admin/`

首次打开后台会进入设置向导：

1. 填写站点和作者基础信息。
2. 创建本地管理员账号。
3. 可选绑定 Li&Pass OIDC。

### 1.2 仅启动公开站

```bash
docker compose up -d
```

公开站是构建后的静态文件；后台未启动时不会自动重建。

## 2. 新建和编辑文章

1. 登录后台。
2. 进入「笔记」→「新建」。
3. 填写标题、日期、状态、标签、摘要、封面和正文。
4. 选择操作：
   - **保存并重建**：保存后触发后台构建。
   - **保存留在本页**：只保存，构建在后台异步执行。
   - **预览**：使用 Hugo 渲染预览。
5. 回收站中的文章可恢复或彻底删除。

文章源文件位于：

```text
content/posts/<slug>.md
```

> 文章与 `mini_json` 已纳入 Git。完成编辑后应提交并推送，确保远端部署包含最新内容。

## 3. 配置小程序同步

### 3.1 什么文章会同步

只有文章编辑器中满足以下条件的条目会进入小程序：

- 文章状态为 `published`
- 不是未来日期文章
- `mini_json.enabled` 为 `true`
- 至少包含一个合法速查条目

文章正文不会进入小程序。

### 3.2 基础示例

在文章编辑器的「小程序同步配置（JSON）」中填写：

```json
{
  "enabled": true,
  "items": [
    {
      "id": "apt",
      "category": "linux",
      "title": "APT 包管理",
      "command": "apt",
      "summary": "Debian / Ubuntu 包管理入口",
      "keywords": ["安装", "卸载", "更新"],
      "tags": ["包管理", "Linux"],
      "syntax": "apt [选项] 操作 [包名]",
      "examples": [
        {
          "label": "刷新软件源索引",
          "code": "sudo apt update"
        }
      ],
      "notes": ["执行安装或升级前先更新软件源索引。"],
      "related": ["apt-get", "dpkg"],
      "order": 10
    }
  ]
}
```

### 3.3 字段规则

| 字段 | 必填 | 规则 |
| --- | --- | --- |
| `id` | 是 | 全局唯一，小写字母、数字和连字符 |
| `category` | 是 | 必须存在于 `config/knowledge.yaml` |
| `title` | 是 | 速查标题 |
| `command` | 是 | 命令、语法或概念名称 |
| `summary` | 是 | 简短说明 |
| `syntax` | 是 | 基本语法 |
| `keywords` | 否 | 参与搜索 |
| `tags` | 否 | 未填写时继承文章标签 |
| `examples` | 是 | 至少一个，含 `label` 与 `code` |
| `notes` | 否 | 使用要点 |
| `related` | 否 | 必须引用存在的速查 `id` |
| `order` | 否 | 数字，越小越靠前 |
| `source_url` | 否 | 默认自动使用文章地址 |

关闭同步：

```json
{"enabled": false}
```

或直接清空编辑器中的小程序同步配置。

## 4. 维护速查分类

后台进入「设置」→「知识速查」。

可编辑：

- 小程序最低支持版本
- 分类 `id`
- 分类显示名称
- 分类简介
- 分类符号

分类 `id` 一旦被文章引用，应保持稳定；只修改显示名称不会破坏同步。

## 5. 构建与发布

保存文章后后台会自动触发构建。手动全量构建：

```bash
docker compose --profile admin run --rm admin python scripts/build.py --full
```

输出：

```text
output/
├── posts/
├── tags/
├── archive/
├── search/
└── knowledge/
    ├── manifest.json
    └── <contentVersion>.json
```

`manifest.json` 包含：

- `schemaVersion`
- `contentVersion`
- `minAppVersion`
- `generatedAt`
- `count`
- `sha256`
- `dataUrl`

内容不变时，`contentVersion` 和 `sha256` 保持不变；`generatedAt` 不参与业务内容签名。

## 6. 更新小程序内置基线

远程热更新使用已发布的 `output/knowledge/`。发布小程序新版本时，如需更新随包基线：

```bash
cd ~/WeChatProjects/miniprogram-1
node scripts/update-builtin.js ~/Desktop/Li\&ProJect/Li\&Notes/output
```

脚本会：

1. 读取 `output/knowledge/manifest.json`
2. 找到对应版本 JSON
3. 校验 schema、分类、标签和引用
4. 重新生成 `data/cheatsheet.builtin.js`

随后重新编译小程序并提交。

## 7. 配置小程序远程域名

编辑：

```text
~/WeChatProjects/miniprogram-1/config/app.js
```

填写：

```js
knowledgeBaseUrl: 'https://你的已备案域名',
knowledgeManifestPath: '/knowledge/manifest.json'
```

然后在微信公众平台：

1. 将域名加入 `request` 合法域名。
2. 确认 HTTPS 证书有效。
3. 确认 `/knowledge/manifest.json` 和版本 JSON 可公开读取。

未配置域名时，小程序继续使用内置基线和本地缓存，不会报功能不可用。

## 8. 备案信息配置

### 8.1 网页端

编辑 `config/brand.yaml`：

```yaml
name: Li&Notes
copyright: © {year} LI&NOTES
icp: 粤ICP备2026008710号-1
icp_url: https://beian.miit.gov.cn/
police: 粤公网安备44010402003600号
police_url: https://beian.mps.gov.cn/
```

显示规则：

- 页脚只展示版权、ICP 备案、公安联网备案。
- ICP 链接指向工信部备案系统。
- 公安备案链接指向 `beian.mps.gov.cn`。
- 任一号码为空时自动隐藏对应条目。
- 禁止使用假占位号。

### 8.2 小程序端

编辑 `~/WeChatProjects/miniprogram-1/config/app.js`：

```js
miniProgramFiling: '', // 真实小程序备案号，未取得时保持空
icp: '粤ICP备2026008710号-1',
icpUrl: 'https://beian.miit.gov.cn/',
police: '粤公网安备44010402003600号',
policeUrl: 'https://beian.mps.gov.cn/',
```

关于页会按字段是否存在自动显示：

- 网站 ICP 备案
- 公安联网备案
- 小程序备案

官方链接通过复制方式提供，不在小程序内直接打开外部网页。

## 9. 日常推荐流程

### 仅新增网页文章

1. 新建文章。
2. 正文、标签、摘要填写完整。
3. 保存并重建。
4. 打开公开站验证。
5. 小程序不会出现该文章。

### 同时新增小程序速查

1. 新建文章并填写正文。
2. 在 `mini_json` 增加一个或多个 `items`。
3. 保存并重建。
4. 确认 `output/knowledge/manifest.json` 的 `count` 增加。
5. 小程序启动或回到前台后自动检查。
6. 在关于页核对内容版本。

## 10. 验证与排查

### 全量验证

```bash
docker compose --profile admin build admin
docker compose --profile admin run --rm -v "$PWD/tests:/app/tests:ro" admin sh -c \
  'unset LINOTES_BOOTSTRAP_BUILD LIBLOG_BOOTSTRAP_BUILD BUILD_TMP_ROOT PREVIEW_ROOT; \
   python -m unittest discover -s tests -q && \
   python scripts/check_hardcoded.py && \
   python scripts/check_contrast.py'
docker compose --profile admin run --rm admin python scripts/build.py --full
```

### 常见错误

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 保存时提示分类不存在 | `category` 不在 `config/knowledge.yaml` | 先增加分类 |
| 提示重复速查 id | 两个条目使用同一 `id` | 改成全局唯一 |
| 提示关联不存在 | `related` 引用了不存在的条目 | 修正或删除该引用 |
| 没有生成 knowledge | 没有启用且合法的 `mini_json` | 检查 `enabled`、状态和示例 |
| 小程序显示“未配置更新地址” | `knowledgeBaseUrl` 为空 | 填写 HTTPS 域名 |
| 小程序请求失败 | 域名不在合法域名列表或证书异常 | 检查公众平台与 HTTPS |
| Hash 不匹配 | 发布数据被截断或手动修改 | 重新执行全量构建并发布 |
| 更新失败但仍能查询 | 回退机制生效 | 保留旧缓存，排查 manifest/data |

### 发布前检查

- `output/knowledge/manifest.json` 存在
- 版本 JSON 存在且无 404
- `count` 与预期速查数量一致
- 小程序关于页显示正确版本和备案信息
- 断网、弱网和坏包时仍可查询
