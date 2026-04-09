# 双色球量子频率分析

该示例脚本展示如何通过 NEUXSBOT 的 MCP REST 数据接口拉取历史开奖，并在本地计算红球 / 蓝球频率与最近组合重叠得分，作为“本地分析程序”输出给用户。

## 运行要求

- 需要 Python 3.10 以上
- 需要联网访问 `https://www.neuxsbot.com/api/v1/mcp/lottery/history`
- 需要有效的 `NEUXSBOT_TOKEN`（可在 [会员中心](https://www.neuxsbot.com/member/api-keys) 生成）

## 配置

创建 `.env`，内容示例：

```
NEUXSBOT_API_BASE_URL=https://www.neuxsbot.com
NEUXSBOT_TOKEN=your-token
```

## 运行

参考 `run.bat`，也可以手动执行：

```powershell
python main.py --periods 120 --output result/ssq.json
```

脚本会输出简体中文摘要，并生成指定路径的 JSON 报告。
