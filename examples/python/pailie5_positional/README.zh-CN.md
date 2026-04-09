# 排列5分析程序

这个示例会连接 NEUXSBOT 的 MCP REST 数据接口，拉取排列5历史数据，然后在本地做位置热度和趋势计算。

## 特点

- 需要联网
- 不需要模型
- 支持 `--periods` 和 `--output`
- 当前实际取数代码使用 `pl5`

## 运行

```bash
python main.py --periods 120
```

如果需要带 Token：

```bash
set NEUXSBOT_TOKEN=你的Token
python main.py --periods 200
```
