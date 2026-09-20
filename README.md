# LangChain 与通义千问作业（完整汇总）

本包汇总此前与本次完成的代码、运行结果、截图及启动工具。已排除个人 API Key、虚拟环境、缓存和重复压缩包。提供的课程 PDF、视频及参考图不是本项目原创成果，未复制到 GitHub 上传包。

## 内容

- `examples/`：基础调用、温度对比、点餐记忆、基础链、扩展链、计算器和时间工具，共七个示例。
- `runs/terminal-screenshots/`：六张真实终端窗口截图，优先用这组作为作业截图。
- `runs/online/`：千问在线运行原始日志、日志页面及页面截图。
- `runs/offline/`：之前的离线教学演示记录，仅作历史留存。
- `终端运行.ps1` / `capture_terminal.ps1`：终端运行和自动截图脚本。
- `capture_runs.py`：在线或离线运行日志页面截图工具。
- `test_examples.py`：本地逻辑测试；`uv.lock`：依赖锁定文件。

## 上传 GitHub

解压后将本文件所在目录的内容上传到仓库。不要只上传 ZIP，这样 GitHub 才能直接显示代码和 README。`.env.example` 是空配置模板；你自己的 `.env` 不在包中，请勿另外上传。

## 在新电脑运行

安装 Python 3.11+ 和 uv，在本文件所在文件夹打开 PowerShell：

```powershell
uv sync --group capture
Copy-Item .env.example .env
```

在 `.env` 中填写自己的 API Key。然后每次执行一组，输出完成后截图：

```powershell
# 1. 基础调用
uv run python examples/class1.py
# 2. 温度对比
uv run python examples/class2_temperature.py
# 3. 点餐对话记忆
uv run python examples/class3_memory.py
# 4. 基础链与扩展链
uv run python examples/06_langchain_chain.py
uv run python examples/07_langchain_long_chain.py
# 5. 计算器
uv run python examples/class5_calc_tool.py
# 6. 时间与星期
uv run python examples/class6_time_tool.py
```

也可双击 `运行全部示例.cmd`。`运行并自动截图.cmd` 需要本机可见的 Windows 桌面，保持终端在前台；它截取当前可见区域，过长输出可能需要手动补截。截图脚本和启动文件已随包保留。

## 之前的详细说明

# LangChain + 通义千问课堂实现

根据提供的《02-LangChain快速入门.pdf》、uv-qwen 视频及六张运行图片实现。

## 当前交付状态

已实现七个脚本，对应六张图。已使用用户本机配置的密钥真实调用 qwen-plus；在线运行日志及六张截图位于 runs/online/。计算器、时钟、消息历史与 LCEL 管道均实际执行。

截图为真实在线运行日志在黑底终端风格页面中的浏览器截图，并非原生 PowerShell/VS Code 窗口截图。TXT 保留完整输出，manifest.json 保存命令、时间及退出码。截图中的模型回复来自千问，未使用离线教学替身。

## 安装及运行

安装 Python 3.11+ 和 uv，在本目录打开 PowerShell：

```powershell
uv sync --group capture
Copy-Item .env.example .env
```

编辑 `.env` 填写自己的 `LLM_API_KEY`。也支持 `DASHSCOPE_API_KEY`。默认模型 `qwen-plus`，默认北京地域兼容地址；若你的账号使用其他地域或专属部署，请填写与密钥对应的地址和模型。

```powershell
uv run python examples/class1.py
uv run python examples/class2_temperature.py
uv run python examples/class3_memory.py
uv run python examples/06_langchain_chain.py
uv run python examples/07_langchain_long_chain.py
uv run python examples/class5_calc_tool.py
uv run python examples/class6_time_tool.py
```

无密钥演示：在任一命令后加 `--offline`。离线广告语是预设教学文本，不能作为模型温度效果的实测结论；真实模式每次向模型发送对应 temperature，结果可能不同，也可能相同。

## 一键执行并生成六张截图

```powershell
# 在线：实际调用千问；结果保存到 runs/online
uv run --group capture python capture_runs.py
# 离线：明确标注替身；结果保存到 runs/offline
uv run --group capture python capture_runs.py --offline
# 测试本地逻辑，不调用 API
uv run python test_examples.py
```

截图器在 Windows 优先使用已安装的 Edge；没有 Edge 时先运行 `uv run --group capture playwright install chromium`，也可通过 `--browser` 指定浏览器可执行文件。截图按完整内容自动调整高度。

## 图片与代码对照

| 原图 | 功能 | 代码 |
|---|---|---|
| 1 | 五轮点餐与完整消息历史 | examples/class3_memory.py |
| 2 | 基础链、分隔线与字数统计 | examples/06_langchain_chain.py、examples/07_langchain_long_chain.py |
| 3 | 简单加法与复杂运算 | examples/class5_calc_tool.py |
| 4 | 当前北京时间与星期 | examples/class6_time_tool.py |
| 5 | 千问自我介绍 | examples/class1.py |
| 6 | temperature 0.0、0.7、1.5 | examples/class2_temperature.py |

## 实现说明

- 采用 `langchain_openai.ChatOpenAI`、`langchain_core` 消息类型及 LCEL；工具通过 `@tool` 声明。在线工具调用使用 `bind_tools → AIMessage.tool_calls → ToolMessage → 模型最终回答` 的有界循环，最多六轮。
- 计算器使用 AST 白名单解析，支持数字、括号、正负号和加减乘除，不使用 `eval`。
- 点餐为教学对话，没有外部餐厅下单系统。每轮传入全部历史。
- 时间读取当前 UTC+08:00 时钟，不复制参考图的日期。
- 讲义的扩展链实际包含五个组件；字符数只统计正文（含标点，不含空白），排除分隔线。
- 源代码不包含视频中的密钥，也不将 `.env` 打包。

接口核对：[LangChain ChatOpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai)、[阿里云兼容接口](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)。
