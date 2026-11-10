# PA Agent — AI 量化交易分析终端

<div align="center">

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-41CD52.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-red.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/recongnize/Trading?style=social)](https://github.com/recongnize/Trading/stargazers)

**本地运行 · 暗黑科技风 · 多数据源 · 两阶段 AI 分析 · 多项目管理**

面向主观交易者的价格行为（Price Action）AI 辅助决策桌面工具。
从 **币安 / TradingView / yfinance / MT5 / AkShare** 读取 K 线，
将结构化数据送入大模型做两阶段分析（市场诊断 → 交易决策）。

> ⚠️ **不是截图识图** · **不连接券商** · **不执行下单**

</div>

---

## ✨ 特性

| 分类 | 功能 |
|------|------|
| 🌐 **数据源** | 币安（默认，加密货币多域名自动回退）、TradingView、yfinance、MT5、AkShare（A 股） |
| 🧠 **AI 分析** | 两阶段：市场诊断 → 策略路由 → 交易决策；增量分析复用上次结论 |
| 📊 **K 线图** | PyQt6 自绘 · 十字光标跟随 · 价格/时间标签 · 真实时间轴 · 大级别联动 |
| 🎨 **UI 风格** | 暗黑科技风 · 玻璃拟态 FlowBar · 脉冲呼吸动画 · 荧光蓝主题 |
| 📁 **多项目管理** | 不同币种独立保存配置、K 线、分析结果 · 一键切换 · 自动恢复上下文 |
| 🔄 **持续跟踪** | 开启后新 K 线收盘自动触发新一轮 AI 分析 |
| 💬 **对话追问** | 分析后自由追问，实时推理流 + Token 进度条 |
| 🛡️ **工程健壮** | JSON 校验 · 截断修复 · 失败自动重试 · API Key 本地加密 |

---

## 🖥️ 界面预览

<div align="center">

### 主界面
> 桌面窗口默认 80% 屏幕尺寸 · 单行紧凑控制栏 · 可收起
>
> (请在此处替换实际运行截图，推荐保存为 `docs/screenshot-main.png`)

### 流程阶段 · 暗黑科技风
> 5 节点 FlowBar · 多层脉冲呼吸发光 · 动态连接线点亮
>
> ![FlowBar 脉冲动画](docs/flow-stage-modal.html)

### K 线交互
> 十字光标 · 价格自适应格式化 · 全屏 40 根视图

</div>

---

## 🚀 快速开始

### 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11（主支持）、macOS 12+ |
| Python | **3.11+** |
| AI API | DeepSeek（推荐，flash 模型便宜且快）、或其他兼容 OpenAI API 的服务 |
| 网络 | 能访问所配置的 AI API 和数据源 |

### 安装

```bash
# 克隆仓库
git clone https://github.com/recongnize/Trading.git
cd Trading

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖（含 PyQt6 GUI）
pip install -e .
```

### 配置 AI API

首次启动后会弹出配置窗口，填入：

```
API Base URL: https://api.deepseek.com
API Key: sk-xxxxxxxxxxxxxxxxxxxx
Model: deepseek-chat  (或 deepseek-flash)
```

配置保存在 `config/settings.json`，**不会**提交到 Git。

### 启动

```bash
# 方式 1：双击（Windows 推荐，无 cmd 黑窗口）
启动PA_Agent.bat

# 方式 2：手动（开发调试用）
python run.pyw       # 无窗口版（推荐）
python run.py        # 带控制台日志
```

### 使用流程

```
1. 选择数据源（默认币安）→ 选交易所/品种/周期
2. 点「获取数据」→ 自动拉取 K 线 + 刷新大级别
3. 点「提交分析」→ AI 两阶段分析（诊断 → 决策）
4. 查看分析结果 · 自由追问
5. 开启「持续跟踪」→ 新 K 线收盘自动分析
6. 左侧项目栏 → 新建/切换项目 · 每个币种独立保存
```

---

## 📁 项目结构

```
Trading/
├── pa_agent/                 # 主包
│   ├── config/               # 配置（Pydantic）
│   ├── data/                 # 数据源（factory + binance_source + tradingview + yfinance）
│   ├── ai/                   # AI 客户端 + Prompt 策略
│   ├── gui/                  # PyQt6 GUI
│   │   ├── main_window.py    #   主窗口（控制栏 + 侧边栏 + 布局）
│   │   ├── project_manager.py#   多项目管理
│   │   ├── widgets/
│   │   │   ├── chart_widget.py   # K 线图（自绘 + 十字光标 + 大级别）
│   │   │   ├── flow_bar.py       #   流程阶段（暗黑科技风 + 脉冲动画）
│   │   │   ├── summary_strip.py  #   信息摘要卡片
│   │   │   └── ai_sidebar.py     #   AI 分析侧边栏
│   │   └── theme/dark.qss   #   暗黑主题样式
│   └── orchestrator/         # 两阶段分析编排
├── prompt_engineering/       # Prompt 模板
├── config/                   # 运行时配置（API Key · 项目列表，自动生成）
├── run.py / run.pyw          # 入口
├── pyproject.toml            # 依赖定义
└── README.md
```

---

## 🔧 数据源配置

### 币安（默认，推荐加密货币）

无需配置，默认走多域名自动回退：
`data-api.binance.vision` → `api1.binance.com` → `api2.binance.com` → `api3.binance.com`

支持品种：`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `DOGEUSDT` 等
支持周期：`1m`, `5m`, `15m`, `1h`, `4h`, `1d`, `1w`

### TradingView

需要在 TradingView 有账号，走 tvDatafeed 库登录。支持全球主要交易所品种。

### yfinance

零配置，支持：`BTC-USD`, `EURUSD=X`, `GC=F`（黄金）等。

### MT5

需要安装 MetaTrader 5 终端并登录账户（Windows 专属）。

---

## 🤝 贡献

欢迎 Issue 和 PR！

```bash
# 开发模式安装
pip install -e .[dev]

# 提交代码
git checkout -b feat/your-feature
git commit -m "feat: add your feature"
git push
```

---

## ⚠️ 免责声明

本工具仅供学习与研究，**不构成投资建议**。
交易有风险，决策后果自负。作者不对任何交易损失承担责任。

---

## 📄 License

[GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE)

如果你在自己的项目中使用了本软件，**必须**公开你的源代码。

---

<p align="center">
  ⭐ 如果这个项目对你有帮助，请点个 Star 支持一下 ⭐
</p>
