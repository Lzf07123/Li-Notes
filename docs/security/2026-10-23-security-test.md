# Li&Notes 安全测试报告

> 日期：2026-10-23 ｜ 范围：Li&Notes 网页端、后台、构建发布、Nginx/容器、Li&知识速查热更新｜ 状态：本地测试通过，待生产部署复核

## 1. 测试范围

- 后台认证、服务端会话、CSRF、登录限速、首次建站保护。
- OIDC 登录、绑定、回调和回程登出。
- Markdown 保存、批量导入、构建期 HTML 安全门禁。
- 图片上传、路径穿越、ZIP 导入、备份恢复与解压限制。
- knowledge manifest/data 同源、Hash、缓存、回退和自动降级。
- Nginx 安全响应头、缓存头、代理来源头与健康检查暴露面。
- Docker 运行用户、只读根文件系统、Docker socket 与敏感文件跟踪状态。
- 直接依赖及完整传递依赖锁定。

## 2. 发现与处置

| 等级 | 发现 | 处置 |
| --- | --- | --- |
| 高 | Pillow 11.3.0、python-multipart 0.0.20 与间接依赖 Starlette 0.52.1 命中已知漏洞 | 升级 FastAPI 0.161.1、Starlette 1.9.0、Pillow 13.0.0、python-multipart 0.0.32，并生成完整 `requirements.lock` |
| 高 | Hugo `unsafe=true`，恶意 Markdown 原始 HTML 可形成存储型 XSS | 保存、导入、构建三层扫描；拒绝脚本/iframe/object/embed/form/svg/style、事件属性、inline style、srcdoc 与危险 URL；代码围栏示例不误报 |
| 中 | `COOKIE_SECURE=1` 的公开首次建站若未配置 `SETUP_TOKEN`，存在被抢先创建管理员的窗口 | HTTPS 首次建站缺少 `SETUP_TOKEN` 时应用拒绝启动 |
| 中 | 后台会话 Cookie 与 OIDC state Cookie 默认作用到整站路径 | 全部限定到 `/<ADMIN_PATH>`，登出删除使用同一路径 |
| 低/误报 | Bandit 报告 MD5 与动态 SQL 字符串 | 非安全用途 MD5 改为 SHA-256；SQL 仅拼接固定占位符片段，用户值全部参数绑定，已审计并加最小 `nosec B608` 标记 |

## 3. 自动化与运行时验证

- Docker 内 **186 项测试通过**；1 项 Nginx 静态测试因 admin 容器未挂载配置目录而跳过，已在宿主单独通过。
- `pip-audit -r requirements.lock`：**No known vulnerabilities found**。
- Bandit 对 `admin/` 与 `scripts/` 的高危/中危扫描：**0 项**。
- Hugo 全量构建通过：**346 pages / 517 files / 15.02 MB**。
- 运行期 UID 1000；根文件系统不可写；容器内无 Docker socket。
- `.env` 当前不存在；`data/.session_secret` 为 `0600`、被 Git 忽略且未被跟踪；常见高置信度密钥模式扫描无命中。
- 真实 Nginx + Admin 栈实测：
  - 后台响应：`Cache-Control: no-store`、`X-Robots-Tag: noindex`、`X-Frame-Options: SAMEORIGIN`、CSP。
  - 会话 Cookie：`HttpOnly`、`SameSite=lax`、`Path=/admin`。
  - 公开站：`X-Frame-Options: DENY`、`Referrer-Policy: no-referrer`、CSP 与 Permissions Policy。
  - `/healthz` 经公开 Nginx 返回 404，未暴露。
  - knowledge manifest：`Cache-Control: no-store, max-age=0`。
- 小程序全量门禁通过，包体积 155.4 KiB；真实 Li&Notes output 经本地 HTTP 联调成功，校验 110 条速查。

## 4. 剩余风险

- 公开站和后台 CSP 仍包含 `script-src 'unsafe-inline'` 与 `style-src 'unsafe-inline'`，原因是模板存在内联脚本和样式。正文安全门禁已降低存储型 XSS 风险；后续仍建议迁移到外链脚本 + CSP hash/nonce。
- 本次未完成基础镜像 OS 包 CVE 扫描：Docker Scout 需要 Docker 账号登录，临时全仓 Trivy 扫描因会暴露本地会话密钥文件而未执行。建议在 CI 中使用固定摘要的扫描器，仅扫描构建上下文或导出的镜像。
- 登录限速为单进程内存实现；若未来改为多 worker/多实例，需要统一到共享限流存储。
- 生产仍需配置真实 TLS、HSTS、`ADMIN_SESSION_SECRET`、`SETUP_TOKEN`、后台路径和 IP 白名单，并完成 OIDC 提供方配置复核。
- 备份 ZIP 含 SQLite、配置和媒体，属于敏感数据，必须限制下载与存放范围。

## 5. 发布门禁

发布前至少确认：

1. `python -m unittest discover -s tests -q` 全部通过。
2. `pip-audit -r requirements.lock` 无已知漏洞。
3. Bandit 无高危/中危。
4. Hugo 全量构建成功，正文安全门禁无误报。
5. 生产 HTTPS 首次建站已设置 `SETUP_TOKEN`。
6. 后台会话 Cookie 为 `Secure`、`HttpOnly`、`SameSite=Lax` 且路径为 `/<ADMIN_PATH>`。
7. 基础镜像 OS CVE 扫描在 CI 或受控环境中完成。
