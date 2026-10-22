---
title: 本站支持哪些 Markdown 语法
date: '2026-08-18'
status: published
tags:
- Markdown
- Hugo
summary: 本站的 Markdown 能力清单：GFM 表格、任务列表、代码高亮、提示块、脚注等。
mini_json: |-
  {
    "enabled": true,
    "items": [
      {
        "id": "heading",
        "category": "markdown",
        "title": "标题",
        "command": "# 标题",
        "summary": "使用 1 到 6 个井号表示标题层级，一级标题通常每个文档只保留一个。",
        "keywords": [
          "标题",
          "h1",
          "h2",
          "heading",
          "层级"
        ],
        "tags": [
          "Markdown",
          "标题",
          "h1",
          "h2"
        ],
        "syntax": "# 一级标题\n## 二级标题\n### 三级标题",
        "examples": [
          {
            "label": "两级标题结构",
            "code": "# 项目说明\n\n## 快速开始\n\n### 安装依赖"
          }
        ],
        "notes": [
          "井号后保留一个空格，否则部分解析器不会识别为标题。",
          "标题层级应连续，避免从一级直接跳到三级。",
          "标题同时服务于目录与无障碍结构，不要只用于改变字号。"
        ],
        "related": [
          "table",
          "code-block",
          "footnote"
        ],
        "order": 230
      },
      {
        "id": "emphasis",
        "category": "markdown",
        "title": "强调与加粗",
        "command": "*强调* / **加粗**",
        "summary": "使用星号或下划线表示斜体与加粗，适合强调关键词，不宜整段滥用。",
        "keywords": [
          "斜体",
          "加粗",
          "强调",
          "italic",
          "bold",
          "emphasis"
        ],
        "tags": [
          "Markdown",
          "斜体",
          "加粗",
          "强调"
        ],
        "syntax": "*斜体* 或 _斜体_\n**加粗** 或 __加粗__",
        "examples": [
          {
            "label": "混合强调",
            "code": "执行 **删除命令** 前，请先确认 *目标范围*。"
          }
        ],
        "notes": [
          "中文正文通常使用星号，避免与词汇中的下划线冲突。",
          "过多加粗会降低层级感，一段只突出最关键的信息。",
          "代码标识应使用行内代码，而不是加粗。"
        ],
        "related": [
          "inline-code",
          "quote",
          "heading"
        ],
        "order": 240
      },
      {
        "id": "link",
        "category": "markdown",
        "title": "链接",
        "command": "[文字](链接)",
        "summary": "使用方括号写显示文字、圆括号写目标地址，可补充悬停标题。",
        "keywords": [
          "链接",
          "url",
          "href",
          "link",
          "引用"
        ],
        "tags": [
          "Markdown",
          "链接",
          "url",
          "href"
        ],
        "syntax": "[显示文字](https://gohugo.io/)",
        "examples": [
          {
            "label": "带标题的链接",
            "code": "[Hugo 文档](https://gohugo.io/ \"Hugo 官方文档\")"
          },
          {
            "label": "引用式链接",
            "code": "[Kubernetes][k8s]\n\n[k8s]: https://kubernetes.io/"
          }
        ],
        "notes": [
          "链接文字应描述目标内容，避免大量使用“点击这里”。",
          "外部链接应确认来源可信，并注意目标站点的隐私政策。",
          "同一链接多次出现时，引用式写法更易维护。"
        ],
        "related": [
          "image",
          "footnote",
          "quote"
        ],
        "order": 250
      },
      {
        "id": "image",
        "category": "markdown",
        "title": "图片",
        "command": "![说明](图片地址)",
        "summary": "在链接语法前加感叹号插入图片，方括号内应写明有用的替代文本。",
        "keywords": [
          "图片",
          "图像",
          "alt",
          "image",
          "资源",
          "路径"
        ],
        "tags": [
          "Markdown",
          "图片",
          "图像",
          "alt"
        ],
        "syntax": "![替代文本](图片地址)",
        "examples": [
          {
            "label": "插入本地图片",
            "code": "![终端输出示例](/images/terminal-output.webp)"
          },
          {
            "label": "带标题的图片",
            "code": "![架构图](/images/architecture.webp \"系统架构\")"
          }
        ],
        "notes": [
          "替代文本不是可选装饰，应描述图片承担的信息。",
          "优先使用 WebP 或 AVIF，并控制图片尺寸。",
          "构建前核对相对路径，避免大小写或目录错误。"
        ],
        "related": [
          "link",
          "code-block",
          "heading"
        ],
        "order": 260
      },
      {
        "id": "unordered-list",
        "category": "markdown",
        "title": "无序列表",
        "command": "- 列表项",
        "summary": "使用减号、星号或加号创建无序列表，通过缩进表达嵌套层级。",
        "keywords": [
          "列表",
          "无序",
          "项目符号",
          "list",
          "ul",
          "嵌套"
        ],
        "tags": [
          "Markdown",
          "列表",
          "无序",
          "项目符号"
        ],
        "syntax": "- 第一项\n- 第二项\n  - 子项",
        "examples": [
          {
            "label": "嵌套列表",
            "code": "- 准备环境\n  - 安装依赖\n  - 检查版本\n- 执行验证"
          }
        ],
        "notes": [
          "同一列表内保持同一种项目符号，便于源码阅读。",
          "嵌套通常使用两个或四个空格，具体取决于所在生态。",
          "列表项较长时可拆成段落，但应保持缩进一致。"
        ],
        "related": [
          "ordered-list",
          "task-list",
          "quote"
        ],
        "order": 270
      },
      {
        "id": "ordered-list",
        "category": "markdown",
        "title": "有序列表",
        "command": "1. 列表项",
        "summary": "使用数字和英文句点表示有先后顺序的步骤，后续编号可由解析器自动维护。",
        "keywords": [
          "列表",
          "有序",
          "步骤",
          "number",
          "list",
          "ol"
        ],
        "tags": [
          "Markdown",
          "列表",
          "有序",
          "步骤"
        ],
        "syntax": "1. 第一步\n2. 第二步\n3. 第三步",
        "examples": [
          {
            "label": "操作步骤",
            "code": "1. 备份当前配置\n2. 应用新配置\n3. 验证服务状态"
          }
        ],
        "notes": [
          "部分解析器会自动重排编号，但源码中仍建议顺序递增。",
          "需要引用具体步骤时，避免频繁插入或删除导致编号漂移。",
          "无序步骤优先使用无序列表，避免制造不存在的顺序。"
        ],
        "related": [
          "unordered-list",
          "task-list",
          "heading"
        ],
        "order": 280
      },
      {
        "id": "inline-code",
        "category": "markdown",
        "title": "行内代码",
        "command": "`代码`",
        "summary": "使用反引号标记命令、文件名、变量名等行内代码，避免与普通正文混淆。",
        "keywords": [
          "代码",
          "行内",
          "命令",
          "变量",
          "inline",
          "code"
        ],
        "tags": [
          "Markdown",
          "代码",
          "行内",
          "命令"
        ],
        "syntax": "`kubectl get pods`",
        "examples": [
          {
            "label": "命令与路径",
            "code": "执行 `kubectl get pods`，并检查 `/etc/nginx/nginx.conf`。"
          }
        ],
        "notes": [
          "内容自身包含反引号时，可使用更多反引号包裹。",
          "行内代码不适合放多行脚本，多行内容使用围栏代码块。",
          "命令与解释之间保留清晰边界，方便复制。"
        ],
        "related": [
          "code-block",
          "emphasis",
          "link"
        ],
        "order": 290
      },
      {
        "id": "code-block",
        "category": "markdown",
        "title": "围栏代码块",
        "command": "```语言 ... ```",
        "summary": "使用三个反引号创建代码块，并在开头标注语言以获得语法高亮。",
        "keywords": [
          "代码块",
          "高亮",
          "bash",
          "yaml",
          "code",
          "fence"
        ],
        "tags": [
          "Markdown",
          "代码块",
          "高亮",
          "bash"
        ],
        "syntax": "```bash\ncommand\n```",
        "examples": [
          {
            "label": "Bash 示例",
            "code": "```bash\nkubectl get pods -A\nkubectl logs -f <pod-name>\n```"
          },
          {
            "label": "YAML 示例",
            "code": "```yaml\napiVersion: v1\nkind: Pod\n```"
          }
        ],
        "notes": [
          "语言标识可帮助构建期高亮，常见值有 bash、yaml、json、python。",
          "复制代码前确认占位符和敏感信息，不要把真实密钥写入示例。",
          "代码块不宜过宽，长命令可使用反斜杠换行。"
        ],
        "related": [
          "inline-code",
          "heading",
          "table"
        ],
        "order": 300
      },
      {
        "id": "table",
        "category": "markdown",
        "title": "表格",
        "command": "| 列1 | 列2 |",
        "summary": "使用竖线和分隔行创建表格，分隔行中的冒号控制列对齐。",
        "keywords": [
          "表格",
          "table",
          "对齐",
          "列",
          "行"
        ],
        "tags": [
          "Markdown",
          "表格",
          "table",
          "对齐"
        ],
        "syntax": "| 左对齐 | 居中 | 右对齐 |\n| :--- | :---: | ---: |\n| A | B | C |",
        "examples": [
          {
            "label": "参数说明表",
            "code": "| 参数 | 说明 |\n| --- | --- |\n| `-A` | 查询全部命名空间 |\n| `-o wide` | 显示扩展信息 |"
          }
        ],
        "notes": [
          "表格前后保留空行，避免被解析为普通段落。",
          "单元格中的竖线需要转义，复杂内容优先使用列表。",
          "移动端宽表格可能横向滚动，列数应保持精简。"
        ],
        "related": [
          "heading",
          "code-block",
          "unordered-list"
        ],
        "order": 310
      },
      {
        "id": "task-list",
        "category": "markdown",
        "title": "任务列表",
        "command": "- [ ] 待办",
        "summary": "在列表项中加入方括号表示未完成或已完成，适合清单与操作核对。",
        "keywords": [
          "任务",
          "待办",
          "勾选",
          "checkbox",
          "task",
          "checklist"
        ],
        "tags": [
          "Markdown",
          "任务",
          "待办",
          "勾选"
        ],
        "syntax": "- [ ] 未完成\n- [x] 已完成",
        "examples": [
          {
            "label": "发布前检查",
            "code": "- [x] 单元测试通过\n- [x] 构建通过\n- [ ] 真机验收"
          }
        ],
        "notes": [
          "方括号内使用一个空格表示未完成，x 表示完成。",
          "并非所有 Markdown 解析器默认启用任务列表扩展。",
          "任务列表适合检查项，不适合承载长段落说明。"
        ],
        "related": [
          "unordered-list",
          "ordered-list",
          "quote"
        ],
        "order": 320
      },
      {
        "id": "quote",
        "category": "markdown",
        "title": "引用块",
        "command": "> 引用内容",
        "summary": "使用大于号创建引用块，适合提示、原文引用或补充说明。",
        "keywords": [
          "引用",
          "提示",
          "quote",
          "blockquote",
          "说明"
        ],
        "tags": [
          "Markdown",
          "引用",
          "提示",
          "quote"
        ],
        "syntax": "> 第一行\n> 第二行",
        "examples": [
          {
            "label": "多行提示",
            "code": "> 执行前先备份配置。\n> 变更后检查服务状态。"
          },
          {
            "label": "嵌套引用",
            "code": "> 外层说明\n>\n> > 内层补充"
          }
        ],
        "notes": [
          "引用不等于语义提示框，重要警告应使用站点提供的短代码或组件。",
          "引用多段内容时保留空引用行。",
          "来源引用应尽量提供可核对的链接。"
        ],
        "related": [
          "link",
          "emphasis",
          "unordered-list"
        ],
        "order": 330
      },
      {
        "id": "footnote",
        "category": "markdown",
        "title": "脚注",
        "command": "文字[^1]",
        "summary": "在正文中标记脚注，并在文末统一定义内容，适合补充来源或额外说明。",
        "keywords": [
          "脚注",
          "注释",
          "来源",
          "footnote",
          "reference"
        ],
        "tags": [
          "Markdown",
          "脚注",
          "注释",
          "来源"
        ],
        "syntax": "正文内容[^1]\n\n[^1]: 脚注说明",
        "examples": [
          {
            "label": "来源脚注",
            "code": "该结论来自官方文档[^official]。\n\n[^official]: 官方文档，访问日期 2026-10-23。"
          }
        ],
        "notes": [
          "脚注标识应保持唯一，定义与引用一一对应。",
          "脚注扩展并非所有 Markdown 解析器默认支持。",
          "链接地址本身可核对时，优先直接使用普通链接。"
        ],
        "related": [
          "link",
          "quote",
          "heading"
        ],
        "order": 340
      }
    ]
  }
---

本站内容全部使用 Markdown 编写，构建期由 Hugo（Goldmark）渲染成静态 HTML，访客浏览器不加载任何 Markdown 解析器。

## 常用语法

| 语法 | 写法 | 效果 |
| --- | --- | --- |
| 表格 | `| 列1 | 列2 |` | 构建期渲染为表格 |
| 任务列表 | `- [x] 完成` | 渲染为勾选列表 |
| 代码块 | 三个反引号 + 语言名 | Chroma 语法高亮 |
| 提示块 | `{{< note >}}...{{< /note >}}` | 纯 CSS 提示框 |
| 脚注 | `文字[^1]` | 页面底部注释 |

```python
def hello():
    return "world"
```

## 提示块示例

{{< note >}}这是一条普通提示。{{< /note >}}

{{< warning >}}这是一条警告提示。{{< /warning >}}

## 脚注示例

这是正文[^1]。

[^1]: 这是脚注内容。
