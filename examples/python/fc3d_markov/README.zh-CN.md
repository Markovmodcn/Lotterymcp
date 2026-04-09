# 福彩3D分析程序

这个示例展示如何使用 NEUXSBOT MCP 的 REST 历史数据，结合本地多指标分析逻辑生成福彩3D分析结果。

## 要点

- 只拉取历史数据，不接模型。
- 依赖 [examples/python/common](../common) 里的 API 客户端和格式化工具。
- 支持 `--periods` 控制读取期数，`--output` 指定 JSON 输出。
- 运行后会打印中文摘要，并写入 `results/fc3d_markov.json`。

## 运行方法

1. 准备环境变量（可选）：
   ```bat
   set NEUXSBOT_API_BASE_URL=https://www.neuxsbot.com
   set NEUXSBOT_TOKEN=<你的会员 Token>
   ```
2. 生成结果：
   ```bat
   run.bat
   ```
3. 查看 `results/fc3d_markov.json`。

## CLI 参数

- `--api-base-url`：默认 `https://www.neuxsbot.com`
- `--token`：使用真 Token 可提升权限
- `--periods`：默认 `100`
- `--output`：默认 `results/fc3d_markov.json`

## 结构说明

- `records`：`numbers_list` 为 `[百, 十, 个]`。
- `recommendations`：综合转移矩阵、和值、跨度、奇偶、类型等维度排序后的推荐结果。
- `validation`：历史长度回测摘要。
