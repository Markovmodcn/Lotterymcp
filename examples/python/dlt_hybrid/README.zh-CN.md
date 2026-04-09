# 大乐透前/后区混合分析

本示例展示如何在本地使用 NEUXSBOT MCP 历史数据接口，计算前区 + 后区频率并合成组合评分，输出实验性推荐组合。

## 运行前准备

- Python 3.10+
- 可访问 `https://www.neuxsbot.com/api/v1/mcp/lottery/history`
- 设置 `NEUXSBOT_API_BASE_URL` 与 `NEUXSBOT_TOKEN`

## 示例命令

```powershell
set NEUXSBOT_API_BASE_URL=https://www.neuxsbot.com
set NEUXSBOT_TOKEN=your-token
python main.py --periods 150 --output result/dlt.json
```

脚本会打印中文摘要并生成 JSON 报告，可以作为“本地分析程序”直接运行，不依赖大模型。
