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

### 2.1 批量导入与模板

后台「笔记 → 导入与导出 → 批量导入与模板下载」提供两份模板：

- **笔记模板**：包含标题、标识、日期、状态、标签、摘要、封面、置顶和正文示例。
- **小程序同步模板**：额外包含可直接校验的 `mini_json` 示例与命令表。

下载并填写后，可以上传多个 `.md` / `.markdown`、整个文件夹或包含 Markdown 的 `.zip`。处理规则：

1. 文件必须是 UTF-8 文本，空文件、NUL 控制字符和无效编码会拒绝导入。
2. `date` 必须是 `YYYY-MM-DD`；`status` 只能是 `published` 或 `draft`。
3. `tags` 支持 YAML 列表或逗号分隔文本，导入时去空、去重。
4. `mini_json` 会在写入前校验 JSON 对象和速查字段，避免坏配置进入构建。
5. 已存在相同 `slug` 时默认跳过；勾选“覆盖同名笔记”才会覆盖，且导入不会额外创建覆盖前快照。

每个文件独立处理。结果页会分别列出成功、跳过和失败原因。单文件、单次总量与文件数量上限由 `IMPORT_MAX_FILE_BYTES`、`IMPORT_MAX_ZIP_BYTES`、`IMPORT_MAX_FILES` 控制。

## 3. 配置小程序同步

### 3.1 什么文章会同步

小程序导出遵守以下优先级：

1. 手写 `mini_json.enabled: true`：直接校验并导出。
2. 未填写 `mini_json`：按 `config/knowledge.yaml` 的自动刮削规则，从「命令速查」表格或允许语言的代码块生成候选。
3. 显式写入 `{"enabled": false}`：永不自动导出。

自动刮削仍只处理已发布、非未来日期、能够匹配速查分类且至少找到一个命令/代码示例的文章。文章正文不会进入小程序。

在后台「跨端 → 小程序同步」可以预览候选、选择文章写回 frontmatter、刷新已持久化配置或清除自动配置。写回后配置带 `generated_by: auto-scrape-v1`，文章仍是唯一内容源。

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

关闭自动同步：

```json
{"enabled": false}
```

清空编辑器中的配置则会重新启用自动刮削；如需永久排除，请保留 `enabled: false`。

## 4. 维护速查分类

后台进入「设置」→「知识速查」。

可编辑：

- 小程序最低支持版本
- 是否自动刮削未手写配置的文章
- 兜底分类、允许的代码语言、单篇条数、示例数与代码长度限制
- 分类 `id`、显示名称、简介、符号
- 分类匹配关键词（逗号分隔）

分类 `id` 一旦被文章引用，应保持稳定；只修改显示名称不会破坏同步。配置保存使用原子写入，容器重建后仍会保留。

## 5. 构建与发布

保存文章后后台会自动触发构建。手动全量构建：

```bash
docker compose --profile admin run --rm admin python scripts/build.py --full
```

输出：

```text
output/
├── index/              # 公开内容索引
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

发布策略：

- `manifest.json` 使用 `Cache-Control: no-store`，确保客户端能及时看到新版本指针。
- 版本 JSON 以内容 Hash 命名，使用长期 `immutable` 缓存。
- 每次构建保留当前与上一版本 JSON；只清理两代以前的文件，避免发布期间的在途请求 404。

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

未配置域名时，小程序继续使用内置基线和本地缓存，不会报功能不可用。只写主机名时客户端会自动补全 `https://`；公网 HTTP 会被拒绝，仅 `localhost`、`127.0.0.1` 与 `::1` 允许用于本地联调。`manifest.dataUrl` 必须与更新域名同源。

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

### 新增含命令表的文章

1. 新建文章，填写正文、标签和摘要。
2. 在 `## 📋 命令速查` 下使用「命令 / 功能 / 注解」表格。
3. 保存并重建。
4. 打开后台「跨端 → 小程序同步」预览候选。
5. 如需持久化，选择文章并点击“写入选中文章并重建”；不写回时构建仍会使用自动候选。
6. 确认 `output/knowledge/manifest.json` 的 `count` 和版本，再在小程序中检查更新。

### 手写或锁定速查

1. 在文章编辑器填写 `mini_json`。
2. 手写配置优先于自动候选。
3. 不希望导出时写 `{"enabled": false}`。

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
| 没有生成 knowledge | 没有手写配置，且自动刮削未匹配分类或示例 | 检查分类关键词、代码语言、文章状态与内容 |
| 自动候选分类错误 | 分类匹配关键词不足或冲突 | 在后台“知识速查”调整分类匹配关键词 |
| 后台写入后重启丢失 | 配置或 content 未挂载到持久化卷 | 检查 Compose bind mount 与目录写权限 |
| 小程序显示“未配置更新地址” | `knowledgeBaseUrl` 为空 | 填写 HTTPS 域名 |
| 小程序请求失败 | 域名不在合法域名列表或证书异常 | 检查公众平台与 HTTPS |
| Hash 不匹配 | 发布数据被截断或手动修改 | 重新执行全量构建并发布 |
| `manifest.dataUrl` 被拒绝 | 数据地址与更新域名不同源或使用 HTTP | 改回同源相对路径 |
| 更新失败但仍能查询 | 回退机制生效 | 查看关于页错误详情，排查 manifest/data |

### 安全验证

容器内回归与审计：

```bash
docker compose --profile admin run --rm -e LIBLOG_BOOTSTRAP_BUILD=0 \
  -v "$PWD/tests:/app/tests:ro" admin sh -c \
  'unset BUILD_TMP_ROOT PREVIEW_ROOT; \
   python -m unittest discover -s tests -q && \
   python scripts/check_hardcoded.py && \
   python scripts/check_contrast.py'
```

依赖与静态扫描：

```bash
docker run --rm -v "$PWD/requirements.lock:/tmp/requirements.lock:ro" \
  python:3.12-slim sh -c 'pip install --quiet pip-audit && pip-audit -r /tmp/requirements.lock'

docker run --rm -v "$PWD:/app:ro" python:3.12-slim sh -c \
  'pip install --quiet bandit && bandit -q -r /app/admin /app/scripts -x /app/tests'
```

正文安全边界：

- 禁止原始 `<script>`、`iframe`、`object`、`embed`、`form`、`svg`、`style` 等高风险标签。
- 禁止内联事件属性、inline `style`、`srcdoc` 与 `javascript:` / `vbscript:` / `data:` URL。
- 上述规则在后台保存、批量导入和全量构建前执行；Markdown 代码围栏与行内代码中的展示文本不会误报。
- `COOKIE_SECURE=1` 且尚未创建管理员时，必须设置 `SETUP_TOKEN`，否则应用拒绝启动，避免公开实例被抢先接管。

### 发布前检查

- `output/knowledge/manifest.json` 存在
- 版本 JSON 存在且无 404
- `count` 与预期速查数量一致
- 小程序关于页显示正确版本和备案信息
- 响应头符合 `manifest: no-store`、版本 JSON: `immutable`
- 断网、弱网、坏包、旧 manifest 与错误缓存时仍可查询
