# LangChain 与 LangGraph 课程作业汇总

本仓库汇总 LangChain 基础作业和 LangGraph 图、状态、控制流、进阶特性及智能问数项目。模型相关示例使用通义千问；数据库和工单使用本地教学数据。

## 作业目录

| 内容 | 位置 | 说明 |
|---|---|---|
| LangChain 基础作业 | [examples](examples) | 7个示例：调用、温度、点餐记忆、链、计算器、时间工具 |
| LangChain 运行说明 | [README_LangChain.md](README_LangChain.md) | 安装、运行与截图说明 |
| LangGraph 完整作业 | [langgraph-coursework](langgraph-coursework) | 26个示例及测试、真实运行日志 |
| 最新6项截图命令 | [命令文件](langgraph-coursework/本次六项截图命令.txt) | 智能问数、三种流、文章子图、客服子图 |
| 前期11栏截图命令 | [命令说明](langgraph-coursework/参考图逐项截图命令.md) | 人工审核、存档、条件、循环、并行、问答等 |
| 原有后端代码 | [backend](backend) | 保留仓库已有内容 |

## 安装运行

先安装 Python 3.11+ 和 uv。在仓库根目录执行 LangChain 作业：

```powershell
uv sync --locked
Copy-Item .env.example .env
uv run python examples/class1.py
```

运行 LangGraph 作业：

```powershell
cd langgraph-coursework
uv sync --locked
Copy-Item .env.example .env
uv run python run_project.py
```

分别在对应目录的 `.env` 配置自己的千问密钥。`run_project.py` 运行最新6项；`run_advanced.py` 运行10至20项；`run_all.py` 运行全部26项。人工审核脚本单独运行会等待yes/no，批量验证明确使用测试审批输入。

## 验证记录

LangGraph 最新31项单元测试通过；六个新增模块已实际调用模型运行。问数示例执行SQLite查询并核对三组金额基准，custom使用模型真实文本流。记录见各项目runs目录。测试命令：

```powershell
uv run python -m unittest discover -p "test_*.py"
```

LangChain 的 `runs/terminal-screenshots` 为终端截图；`runs/online` 包含在线日志及日志页面截图；`runs/offline` 为早期离线演示历史资料，不作为在线运行证明。历史资料保留原标注。

## 文件约定

- 不提交 `.env`、API密钥、虚拟环境、缓存或本地数据库。
- `.env.example` 为可公开的空配置模板。
- 运行时自动生成示例数据库；不连接真实业务库，不发送外部客服通知。
- 课程PDF、视频与同学参考图未复制进本仓库。
- 保留原有仓库内容；与本地同名但不同的基础作业文件放在 `langchain-local-updates`（如存在）。
