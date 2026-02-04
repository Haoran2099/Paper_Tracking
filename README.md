# Paper Tracker

每日自动追踪 arXiv 论文，使用 AI 进行分析和分类，生成静态网站展示。

**在线演示**: [https://haoran2099.github.io/Paper_Tracking/](https://haoran2099.github.io/Paper_Tracking/)

## 界面预览

| 首页 | 论文详情 |
|:---:|:---:|
| 高相关度论文 + 最新论文列表 | AI 摘要 + 主要贡献 + 方法论 |

**主要页面:**
- **首页**: 高相关度论文卡片、最新论文列表、分类导航
- **分类页**: 论文筛选（按日期/相关度排序，按分数过滤）
- **详情页**: AI 生成的中文摘要、主要贡献、方法论分析、原文摘要

## 特性

### 核心功能
- **多领域支持**: 通过 `config.json` 自定义追踪任意研究领域
- **多 LLM 支持**: Claude / OpenAI / Gemini / Ollama / MiniMax
- **自动化部署**: GitHub Actions 每日自动更新 + GitHub Pages 托管
- **AI 分析**: 自动生成中文摘要、主要贡献、方法论、相关度评分

### 前端界面
- **深色主题**: Research Observatory 风格，类似 GitHub Dark
- **精选字体**: JetBrains Mono (代码) + Instrument Sans (标题) + Source Serif 4 (正文)
- **客户端搜索**: 实时搜索论文标题、摘要、标签，支持键盘导航
- **响应式设计**: 完美适配桌面和移动端
- **流畅动画**: 页面加载渐入效果、悬停交互动画
- **论文卡片**: 相关度评分高亮、标签展示、一键访问 PDF

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt

# 根据使用的 LLM 安装额外依赖
pip install google-generativeai  # Gemini
```

### 2. 配置

复制并编辑配置文件：

```bash
cp .env.example .env
# 编辑 .env 设置 API Key
```

编辑 `data/config.json` 自定义追踪领域和 LLM 提供商。

### 3. 运行

```bash
# 获取并分析论文
python -m src.main fetch-and-analyze

# 生成静态网站
python -m src.main generate-site

# 本地预览
python -m src.main serve
```

## 支持的 LLM 提供商

| 提供商 | provider | 模型示例 | 环境变量 |
|--------|----------|----------|----------|
| Claude | `claude` | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai` | `gpt-4o-mini` | `OPENAI_API_KEY` |
| Gemini | `gemini` | `gemini-2.0-flash` | `GOOGLE_API_KEY` |
| Ollama | `ollama` | `llama3.2` | - |
| MiniMax | `minimax` | `abab6.5s-chat` | `MINIMAX_API_KEY` |

## CLI 命令

| 命令 | 说明 |
|------|------|
| `show-config` | 显示当前配置 |
| `fetch-and-analyze` | 获取并分析论文 |
| `generate-site` | 生成静态网站 |
| `run` | 执行完整流程 |
| `serve` | 启动本地预览服务器 |

### 选项

| 选项 | 适用命令 | 说明 |
|------|---------|------|
| `--config, -c` | 全局 | 指定配置文件路径 |
| `--days, -d` | `fetch-and-analyze` | 回溯天数（默认 1） |
| `--dry-run` | `fetch-and-analyze` | 仅获取不分析 |
| `--output, -o` | `generate-site`, `serve` | 输出目录（默认 `docs`） |
| `--port, -p` | `serve` | 服务器端口（默认 8000） |

## 配置说明

`data/config.json` 示例：

```json
{
  "site": {
    "title": "My Paper Tracker",
    "description": "Tracking papers in my research areas",
    "base_url": "/Paper_Tracking"
  },
  "llm": {
    "provider": "gemini",
    "model": "gemini-2.0-flash",
    "api_key_env": "GOOGLE_API_KEY"
  },
  "domains": [
    {
      "name": "LLM Memory",
      "categories": ["cs.CL", "cs.AI"],
      "keywords": ["memory", "RAG", "retrieval"],
      "output_category": "memory"
    }
  ],
  "fetch": {
    "days_back": 1,
    "max_papers_per_domain": 50,
    "min_relevance_score": 5
  }
}
```

> **注意**: `base_url` 用于 GitHub Pages 部署，格式为 `/<repo-name>`。本地开发时可设为空字符串 `""`。

## GitHub Actions 部署

1. Fork 本仓库
2. 设置 Repository Secret（根据你选择的 LLM 提供商）:
   - Claude: `ANTHROPIC_API_KEY`
   - OpenAI: `OPENAI_API_KEY`
   - Gemini: `GOOGLE_API_KEY`
3. 启用 GitHub Pages（Settings → Pages → Source: GitHub Actions）
4. 工作流每日 UTC 6:00（北京 14:00）自动运行

## 项目结构

```
Paper_Tracking/
├── .github/workflows/
│   └── daily_update.yml     # GitHub Actions 自动化
├── src/
│   ├── main.py              # CLI 入口
│   ├── config.py            # 配置管理 (Pydantic)
│   ├── models.py            # 数据模型
│   ├── arxiv_fetcher.py     # arXiv API 封装
│   ├── site_generator.py    # 静态网站生成器
│   └── llm/                 # 多 LLM 支持
│       ├── base.py          # 抽象基类
│       ├── claude_analyzer.py
│       ├── openai_analyzer.py
│       ├── gemini_analyzer.py
│       ├── ollama_analyzer.py
│       └── minimax_analyzer.py
├── templates/               # Jinja2 模板
│   ├── base.html           # 基础布局
│   ├── index.html          # 首页
│   ├── paper_list.html     # 分类列表页
│   └── paper_detail.html   # 论文详情页
├── static/
│   ├── css/style.css       # 深色主题样式
│   └── js/main.js          # 客户端搜索
├── data/
│   ├── config.json         # 用户配置
│   └── papers/             # 论文 JSON 数据
└── docs/                    # 生成的静态网站
```

## License

MIT

