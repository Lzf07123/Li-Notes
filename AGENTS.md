# Li&Notes 项目协作手册

## 事实来源（按优先级）

| 层级 | 文件 | 职责 |
| --- | --- | --- |
| 设计意图 | `design-system/notes/BRAND.md` | 定位、边界、视觉原则与体验底线 |
| 实现速览 | `design-system/notes/MASTER.md` | 路由、数据、后台、构建与验收 |
| 设计文档 | `docs/superpowers/specs/` | 系统设计事实与跨端契约 |
| 代码事实 | `themes/blog-theme/static/css/tokens.css` + `config/*.yaml` | 令牌与品牌/作者/文案唯一出处 |
| 模板参考 | `design-system/Li-Design/` | 家族模板与组件规格，仅参考 |

冲突时以代码事实为准，并同步回写 BRAND / MASTER / 设计文档，防止漂移。

## 项目边界

Li&Notes 只负责完整文章域：首页、文章列表、详情、标签、归档、搜索和后台编辑。以下内容不属于本项目：

- 个人主页式 Hero、技能徽章、项目集、时间线、关于页、资源页、友情链接。
- 博客镜像式小程序、文章评论、留言、注册、登录用户端。
- 运行时 Markdown 解析、远程字体、CDN 脚本与远程效果包。

`themes/blog-theme/` 和 `--liblog-*` 是内部兼容命名，暂不作为产品名；重命名必须单独迁移。

## 硬性规则

1. **单一事实来源**：品牌文案只存 `config/brand.yaml`；作者资料只存 `config/profile.yaml`；站点文案只存 `config/strings.yaml`；颜色/阴影/动效只存 `tokens.css`。组件禁止硬编码可见文案与裸 hex。
2. **公开站零交互**：不得引入评论、留言、注册、登录、表单或用户输入栏目。
3. **全站可见内容后台可改**：新增可见内容必须同步后台入口并更新 `design-system/notes/MASTER.md`。
4. **备案红线**：备案号禁止假占位；页脚备案链接指向官方域名；公开站不收集个人信息。
5. **秘密与安全**：OIDC secret、密码等只走环境变量/.env/secret 文件；后台路径保持秘密；禁止 Docker socket；运行期以 UID 1000 非 root 运行。
6. **Markdown 为内容源**：文章与页面使用 Markdown/YAML，构建期渲染，禁止公开页运行时 Markdown 解析。
7. **性能底线**：公开站纯静态；动效尊重 `prefers-reduced-motion`；禁止外部 CDN、远程字体和远程 JS。
8. **构建约束**：Hugo 固定 v0.165.0（`bin/hugo/`，SHA256 校验）；构建必须走校验 → `GOMEMLIMIT` 限内存渲染 → 逐文件原子发布 → 清理；部署域名由 `SITE_BASEURL` 注入；渲染器只用 Hugo。
9. **后台安全**：PBKDF2-HMAC-SHA256 600k；服务端会话、CSRF、登录限速；OIDC 遵循 PKCE/state/nonce/验签/防重放；上传白名单与大小限制；预览走 Hugo。
10. **依赖与运行期**：apt/pip 使用镜像变量；Hugo 不联网下载；Fuse.js 等前端库必须本地化；`content/ config/ output/` 使用 bind 挂载，`data/ media/` 使用命名卷。
11. **跨端数据**：小程序只消费文章 `mini_json` 导出的结构化速查数据与版本清单，不镜像文章正文或执行远程代码；分类/最低版本存 `config/knowledge.yaml`，构建后必须生成 `output/knowledge/manifest.json` 与版本 JSON。
12. **验证环境**：调试和构建优先使用 Docker；不得为日常验证在宿主机安装 Hugo、Python 依赖或前端工具链，任务结束清理临时容器/卷/文件。

## 协作规范

- 并行任务零文件重叠；需要改他人文件先认领并经 root 同意。
- 不擅自切分支或合并；不覆盖未提交改动。
- 验证才算完成：必须给出构建、测试、页面或令牌检查证据。
- 验收以证据为准，不接受无证据的“完成”。

## 常用验证（Docker 优先）

```bash
docker compose --profile admin build admin
docker compose --profile admin run --rm -v "$PWD/tests:/app/tests:ro" admin sh -c \
  'unset LINOTES_BOOTSTRAP_BUILD LIBLOG_BOOTSTRAP_BUILD BUILD_TMP_ROOT PREVIEW_ROOT; \
   python -m unittest discover -s tests -q && \
   python scripts/check_hardcoded.py && \
   python scripts/check_contrast.py'
docker compose --profile admin run --rm admin python scripts/build.py --full
```

不得为日常调试在宿主机安装 Hugo、Python 依赖或前端工具链；Docker 不可用时才使用临时环境，并在任务结束清理。

## 多 Agents 协作

任务卡写明 Consumes 与 Produces（精确到文件）及可独立验证的验收标准；root 负责拆解、指派与验收，槽位类决策必须由本人拍板。
