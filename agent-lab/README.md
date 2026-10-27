# Agent Lab · 商城智能体测评中心

本项目对应两项作业：**10.20 智能体测评体系搭建**、**10.22 智能体改造设计**。从零实现商城场景的测评实验台，不是完整电商交易网站。界面参考用户提供的紫色评测中心截图，数据来自实际执行。

## 启动

安装 Python 3.11+ 和 uv，在此目录运行：

```powershell
uv sync --frozen
uv run python -m app.evaluation
uv run uvicorn app.main:app --host 127.0.0.1 --port 8017
```

打开 http://127.0.0.1:8017/ ，API 文档 http://127.0.0.1:8017/docs 。本地也可运行 `start.ps1`。默认回放不需要 API Key。仅绑定本机，不要直接对公网部署此教学沙箱。

## 两项提交入口

| 作业 | 页面 | 源码与材料 |
|---|---|---|
| 10.20 测评体系搭建 | 评测中心、黄金数据集 | `app/evaluation.py`、`eval/datasets/shop-v1.json`、`app/judge.py`、`artifacts/latest.json` |
| 10.22 改造设计 | 改造设计 | `app/design.py`、`app/agent.py`、`docs/10.22-智能体改造设计.md` |

截图位于 `evidence/`。JSON 快照含时间、版本、数据集 SHA-256、逐条断言、原始输出和工具执行记录。截图是浏览器对实际运行页面的捕获，没有使用绘图模型生成。

## 实测结果与解释

2026-10-27 的确定性回放：v1 **8/15**，v2 **15/15**，v2 字段/状态断言 **28/28**；自动化检查 **31 passed**。最终运行时间见 `artifacts/latest.json`，耗时因机器运行状态会变化。

评分公式为通过用例数 / 总用例数 × 100，各维度按带相应标签的用例统计，同一用例可能属于多个维度。100 分表示这 15 条固定回放用例全部通过，不表示真实模型完美或完整商城已验收。

v1 是本项目新建的教学对照实现：单次调用、严格 JSON 解析、不做按能力的工具白名单。v2 才增加容错解析、工具和参数校验、反馈修复和限次控制。两者都保留底层数据库只读隔离，不为制造分差而执行危险 SQL。两者接收同一个故障脚本；失败后 v2 才会请求脚本的下一响应。

## 真实 Qwen 与语义 Judge（可选，未作为本次成绩来源）

统一接入层是 `app/providers.py:get_llm`，使用 `ChatOpenAI`；Judge 使用 `with_structured_output`。配置通过进程环境变量读取，`.env.example` 只用于说明，不自动加载 `.env`。

```powershell
# 在自己的终端中设置 DASHSCOPE_API_KEY，不要提交密钥。
$env:LLM_MODEL_ID='qwen-plus'
$env:JUDGE_MODEL_ID='qwen-max'
uv run python -m app.evaluation --provider qwen
uv run python -m app.judge artifacts/latest.json
```

在线评测会调用付费模型。问题、上下文发给模型，参考答案和回放脚本不发给模型。回放故障如围栏/缺字段不保证在真实模型运行中出现，因此在线分数不能直接和回放分数比较。当前界面默认用于回放，浏览器按钮只触发回放。

人工校准：先由真人对同一输出版本按 `app/judge.py` 的 1/3/5 锚点评分，至少 3 条（建议 5 条以上），输入结构见 `docs/人工校准说明.md`。未提供真人标注，不能声称 MAE 达标；本项目没有编造人工分数。

## 测试与边界

```powershell
uv run pytest -q
```

覆盖黄金用例、恶意 SQL、工具越权、重复失败操作、上下文隔离、错误结果检出、人工评分来源与快照匹配、接口及方案绑定。

- SQLite 内存数据为固定教学样例，非真实商户数据；每次工具查询新建隔离连接。
- 客服上下文由用例显式提供，未实现跨用户持久化聊天系统。
- 规划记录是原始结构化输出/工具参数/观察结果，不是模型隐藏思维链。
- PDF 中完整学习教练、并行纠错、生词库、持久化 Checkpointer 等属于英语学习助手后续模块，未冒充为本次商城两项作业已实现功能。
