# Li&Notes 实现速览

> 版本：v2.6 ｜ 日期：2026-10-23 ｜ 技术栈：Hugo + FastAPI + SQLite + Nginx

## 1. 结构

```text
content/posts/          # 唯一文章内容源
config/brand.yaml       # 品牌/版权/备案
config/profile.yaml     # 作者姓名和外部链接
config/strings.yaml     # 导航/文案/空状态
config/knowledge.yaml   # 小程序分类、自动刮削规则
content/content-index/  # 公开内容索引
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
| `/index/` | 按年份与主题组织的公开内容索引 |
| `/tags/` | 标签索引 |
| `/tags/<tag>/` | 标签文章列表 |
| `/search/` | 构建期 JSON 搜索索引 |

已移除：`/projects/`、`/timeline/`、`/about/`、`/resources/`、`/friends/`。

## 3. 后台

| 分组 | 栏目 |
| --- | --- |
| 内容 | 文章、标签、回收站 |
| 设置 | 品牌、文案、作者资料、知识速查规则、账号 |
| 跨端 | 内容索引健康、搜索索引状态、自动刮削预览/持久化、knowledge manifest |
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
- 小程序速查优先生效手写 `mini_json`；未配置时按 `config/knowledge.yaml` 自动刮削命令表或代码块。
- 后台确认的自动候选写回文章 frontmatter，并带 `generated_by: auto-scrape-v1` 标记。
- `--full` 构建输出 `output/knowledge/manifest.json` 和带版本 JSON。
- manifest Hash 只签名业务内容，`generatedAt` 不得造成同版本 Hash 漂移。

## 5. 构建与验证

```bash
python -m unittest discover -s tests -q
python scripts/check_hardcoded.py
python scripts/check_contrast.py
HUGO_BIN=/path/to/hugo-0.165.0 python scripts/build.py --full
```

门禁包括：JSON/XML 产物、搜索索引字段/唯一 URL、公开内容索引页、内部链接、草稿泄漏、未来文章、静态资源缺失、占位域名与关键文本对比度。

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

## 8. 公开站阅读体验

- 首页先展示紧凑的学习档案摘要（笔记数、主题数、最近更新），再直接进入笔记流，不扩展为个人主页 Hero。
- 笔记、标签与归档页共用页面标题层级：来源眉题、唯一 H1、简述与统计；归档与标签按内容关系组织，不做装饰性时间线。
- 文章页只保留模板生成的唯一 H1；桌面端目录固定在正文右侧，视口 ≤1200px 时折叠为原生可键盘操作的 `details`；正文列始终在视口中心。
- 移动端主导航固定保留首页与搜索，“更多”菜单提供笔记、归档和内容索引入口。

## 9. 索引与小程序自动化

1. Hugo 构建 `/search/index.json` 并生成 `/index/`；构建门禁校验索引字段完整且 URL 唯一。
2. 后台“跨端 → 内容索引”读取搜索索引、公开索引与 knowledge manifest，展示数量、时间、版本和 Hash 校验状态。
3. 自动刮削只处理 `published` 且非未来文章；手写 `mini_json` 与显式 `enabled: false` 优先。
4. 命令表优先按行抽取；无命令表时从允许语言的代码块生成一篇一条的速查候选。
5. 候选先预览，确认后写回文章 frontmatter；配置和 Markdown 均使用临时文件、`fsync` 与 `os.replace` 原子持久化。
6. 小程序热更新先校验证书/同源/体积/schema/引用/Hash，再替换缓存；缓存持久化 contentVersion 与 SHA-256，启动时复核。
7. 自动检查并发请求合并为单一 in-flight；成功后节流 5 分钟，失败后 60 秒可重试，手动检查绕过节流。
8. 自动检查按 `generatedAt` 防止远端旧包静默降级；手动检查保留强制回滚能力。
9. 构建保留当前与上一版本 knowledge JSON；Nginx 对 manifest 返回 `no-store`，对版本 JSON 返回一年 `immutable`。

## 10. 响应式排版契约

- 公开站以 320px 为最小验收宽度；页面不得出现文档级横向滚动，长标题使用自然平衡换行，禁止强制 `<br>` 或截断可见正文。
- 元信息采用可换行的 flex 布局；内容索引条目在 ≤900px 改为单栏；文章数据表在 ≤640px 通过 `responsive-tables.js` 转为带字段名的卡片。
- 后台侧栏在 ≤1280px 切换为顶部横向导航；≤768px 不再粘滞，避免窄屏持续占用视口；≤600px 导航筛选框独占一行。
- 后台文章/配置/同步表格使用 `table-shell--cards`；移动端配置字段纵向排列，操作按钮可换行，长标题禁止省略号截断。
- 登录页在 ≤820px 将页脚移出绝对定位，≤480px 隐藏装饰侧栏并显示紧凑品牌行，保证主按钮不被覆盖。
- 验收矩阵：公开站 320/360/390/768/1024/1280/1440；后台 320/360/390/768/1024/1280/1281/1366/1440。

## 11. 视觉质感层

- 颜色、字体栈、纸页表面、细线、网格、光环和阴影均定义在 `themes/blog-theme/static/css/tokens.css`；`style.css` 末尾的“知识档案质感层”只消费令牌。
- 新增 `--liblog-font-display`、`--liblog-font-reading`、`--liblog-font-label`，全部使用本地字体回退，不请求远程字体。
- 首页使用档案式大标题、统计刻度条与编号笔记卡；列表/归档继承同一细线和标签语法。
- 文章页使用衬线阅读正文、纸页式目录、编号示例与结构化代码表面；≤1200px 目录折回正文上方，正文保持居中；≤640px 隐藏卡片编号并压缩留白。代码复制按钮位于独立外壳，不随代码横向滚动。
- 交互层只做轻微抬升、边框主色化与阴影变化，继续遵守 `prefers-reduced-motion`；320px 无横向溢出的响应式契约不变。
- 小程序共享表面、网格、字号与徽记语法，但采用“随身速查卡”组件：分类单字徽记、命令块、示例编号和搜索聚焦光环。

## 12. 安全基线

- 后台会话 Cookie 使用 `HttpOnly`、`SameSite=Lax`，路径限定到 `/<ADMIN_PATH>`；OIDC state Cookie 同样限定路径。
- `COOKIE_SECURE=1` 的 HTTPS 首次建站必须配置 `SETUP_TOKEN`，否则启动失败，防止公开实例被抢占。
- Markdown 正文在保存、导入与构建前扫描危险原始 HTML；脚本、iframe/object/embed/form/svg/style、内联事件、inline style、srcdoc 与危险 URL 均被拒绝，代码围栏示例除外。
- Nginx 覆盖客户端 `X-Forwarded-For`，登录限速和 IP 白名单只信任边缘代理写入的真实来源。
- 运行期 UID 1000、只读根文件系统、无 Docker socket；后台响应统一 `no-store`、`noindex` 与 CSP。
- 依赖精确锁定；发布前运行 `pip-audit` 与 Bandit，生产 TLS、真实 `SETUP_TOKEN` 和 OS 镜像 CVE 扫描仍需部署验收。
