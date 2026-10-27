from app.evaluation import load_dataset

def designs():
    data=load_dataset()
    specs=[("customer","智能客服","商品查询、上下文引用、投诉转人工","先规划 → 工具权限校验 → 参数校验 → 检索/转人工 → 证据输出",["客服不能调用销售查询工具","商品缺失时不得捏造价格","记忆必须由可信会话上下文提供"]),
        ("data","销售问数","汇总、地区时间筛选、商品排行","生成 SELECT → 权限校验 → SQLite 只读执行 → 错误反馈 → 限次修复",["只允许 sales 表及白名单聚合函数","禁止写入、ATTACH、PRAGMA 和多语句","错误 SQL 最多尝试三次，重复失败操作提前停止"]),
        ("scene","营销场景","场景目标、角色和任务步骤","素材输入 → 结构化规划 → Pydantic 校验 → 失败反馈 → 合格结果",["至少两个角色、三个任务步骤","禁止场景工具读取销售和商品数据","无法校验时明确失败，不保存无效场景"])]
    return [{"id":target+"-design-v1","target":target,"name":name,"version":1,"status":"draft","goal":goal,"flow":flow,"boundaries":bounds,
        "dataset_fingerprint":data["fingerprint"],"bound_cases":[c["id"] for c in data["cases"] if c["target"]==target],
        "actions":[{"component":"编排","change":"v1 单次严格 JSON 调用改为 v2 plan → validate → execute → finish 状态图；失败条件边最多三次尝试。"},
                   {"component":"可观测性","change":"保存原始输出、工具参数、执行结果、错误、尝试次数与节点顺序；不展示或伪造模型隐藏思维链。"},
                   {"component":"测评","change":"固定数据集 SHA-256 + 同输入 v1/v2 比较 + 逐条断言；人工语义校准独立进行。"}],
        "acceptance":"绑定用例全部通过；安全边界不得因改造退化。语义效果需在线 Judge 与真实人工标注后另行验收。"} for target,name,goal,flow,bounds in specs]
