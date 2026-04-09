# 排列3分析程序

本示例通过排列3历史数据构建本地综合分析逻辑，结合 NEUXSBOT MCP REST 接口，生成中文摘要和 JSON 结果。

## 要点

- 不依赖模型，只拉数据+本地算法。
- 复用 `examples/python/common` 里的 API 客户端/格式化。
- 支持 `--periods` 控制读取数量，`--output` 控制 JSON 位置。
- 默认会写入 `results/pl3_markov.json` 并打印热度。

## 快速运行

1. (可选) 设置 `NEUXSBOT_API_BASE_URL`、`NEUXSBOT_TOKEN`。
2. 执行：
   ```bat
   run.bat
   ```
3. 查看输出文件或控制台总结。

## 参数

- `--api-base-url`：MCP REST 地址，默认 `[https://www.neuxsbot.com](https://www.neuxsbot.com)`。
- `--token`：会员 Token，非必需。
- `--periods`：默认 `120`，可调整历史深度。
- `--output`：默认 `results/pl3_markov.json`。
