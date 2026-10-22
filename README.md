# Li&Notes

> 一次记录，见证每一步成长。

Li&Notes 是个人学习笔记站，负责完整 Markdown 笔记的写作、归档、标签、搜索与静态发布。公开站保持纯静态、零交互入口；后台按需启动。

## 边界

- 只承载文章：首页、文章列表、文章详情、标签、归档、搜索。
- 不承载个人展示、项目集、时间线、关于页、资源页或友情链接。
- 微信小程序“知识速查”只消费从笔记中整理出的结构化速查数据，不镜像文章正文。
- 跨端方案见 `docs/superpowers/specs/2026-10-23-notes-knowledge-coexistence.md`。

## 使用方法

完整操作流程见 [docs/USAGE.md](docs/USAGE.md)：启动、后台写作、小程序速查配置、构建发布、热更新、备案信息和故障排查。

## 技术栈

- Hugo 0.165.0：Markdown 构建期渲染、Chroma 高亮、搜索索引。
- FastAPI + SQLite：单管理员后台、文章编辑、修订、媒体、备份与统计。
- Nginx：静态产物、匿名打点与后台反向代理。
- 原生 CSS 与本地 JS：无外部 CDN、远程字体或运行时 Markdown 解析器。

## 功能

- Hugo 固定版本分段构建：校验 → 限内存渲染 → 目录内逐文件原子发布。
- 内容体检：内部链接、图片、空正文、短摘要、重复标题与超长标题。
- 后台文章管理：状态、标签、置顶、封面、摘要、批量操作、CSV 导入导出。
- 修订历史、回收站、媒体库、备份恢复与操作审计。
- Fuse.js 本地搜索，构建期生成索引。
- 阅读进度、代码复制、目录、上一篇/下一篇与相关笔记。
- 明暗主题跟随系统。
- 文章可配置 `mini_json`，构建期导出小程序速查包与 `manifest.json`。
- 访问统计只记录路径与时间，不收集访客个人信息。

## 本地运行

```bash
docker compose up -d
docker compose --profile admin up -d
```

默认公开站端口 `80`；可在 `.env` 设置 `HTTP_PORT`。首次部署无需手动构建，admin 启动会自动执行全量构建；设置 `LINOTES_BOOTSTRAP_BUILD=0` 可关闭（旧变量 `LIBLOG_BOOTSTRAP_BUILD` 仍兼容）。

部署前在 `.env` 设置 `SITE_BASEURL=https://你的域名/`；启用 HTTPS 后将 `COOKIE_SECURE=1`。

## 小程序内容同步

文章编辑器中的“小程序同步配置（JSON）”使用：

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
      "keywords": ["安装", "卸载"],
      "tags": ["包管理", "Linux"],
      "syntax": "apt [操作] [包名]",
      "examples": [{"label": "更新索引", "code": "sudo apt update"}],
      "notes": ["执行前先更新索引"],
      "related": ["apt-get"]
    }
  ]
}
```

`--full` 构建会在 `output/knowledge/` 生成：

- `manifest.json`
- `<contentVersion>.json`

小程序只消费该结构化数据，不镜像文章正文。分类名称在后台“知识速查”中维护。

## 验证（推荐 Docker）

```bash
docker compose --profile admin build admin
docker compose --profile admin run --rm -v "$PWD/tests:/app/tests:ro" admin sh -c \
  'unset LINOTES_BOOTSTRAP_BUILD LIBLOG_BOOTSTRAP_BUILD BUILD_TMP_ROOT PREVIEW_ROOT; \
   python -m unittest discover -s tests -q && \
   python scripts/check_hardcoded.py && \
   python scripts/check_contrast.py'
docker compose --profile admin run --rm admin python scripts/build.py --full
```

宿主机不安装 Hugo、Python 依赖或前端工具链。仅在 Docker 不可用时，才使用与 `requirements.txt` 一致的本地 Python 环境。

## 目录

```text
content/                  # 文章与页面 Markdown（当前仅文章域）
config/                   # 品牌、作者、站点文案
admin/                    # FastAPI 管理后台
themes/blog-theme/        # Hugo 主题兼容路径（对外内容为 Li&Notes）
design-system/notes/      # Li&Notes 品牌与实现事实源
design-system/Li-Design/  # 家族模板参考（git 子模块）
scripts/                  # 构建、硬编码与对比度检查
tests/                    # 单元与回归测试
```

> `themes/blog-theme/` 与 `--liblog-*` 令牌是内部兼容命名，不是站点定位；后续如重命名，必须配套数据卷、备份恢复和缓存迁移。

## 配置事实源

| 内容 | 唯一来源 |
| --- | --- |
| 品牌、版权、备案 | `config/brand.yaml` |
| 作者姓名与链接 | `config/profile.yaml` |
| 导航、页面文案、空状态 | `config/strings.yaml` |
| 颜色、阴影、动效 | `themes/blog-theme/static/css/tokens.css` |
| 文章与小程序速查配置 | `content/posts/*.md` |
| 小程序分类与最低版本 | `config/knowledge.yaml` |

## 备案与安全

- 页脚只保留版权、ICP 备案和公安联网备案，其他非必要法律/内容声明已移除。
- ICP 链接指向工信部备案系统，公安备案链接指向 `beian.mps.gov.cn`；号码为空时自动隐藏。
- 不展示假备案号；备案信息只从 `brand.yaml` 读取。
- 公开站不收集访客个人信息，无评论、留言、注册或用户输入入口。
- 后台密钥只通过环境变量或 `data/.session_secret` 保存，不进入 Git。
- 媒体上传只允许白名单图片格式，并限制大小与路径。
