# Lotterymcp Python 本地分析程序

这一组示例适合不直接接大模型、想先在本地跑算法的人。

它们会联网读取网站历史开奖数据，然后在本地执行分析逻辑，适合作为研究、演示、二次开发和后续打包 EXE 的基础版本。

## 当前包含的示例

- `fc3d_markov`：福彩 3D 分析程序
- `pl3_markov`：排列 3 分析程序
- `ssq_quantum`：双色球分析程序
- `dlt_hybrid`：大乐透分析程序
- `pailie5_positional`：排列 5 分析程序
- `select7_positional`：七星彩分析程序
- `kl8_frequency`：快乐 8 分析程序

## 运行前准备

1. 安装 Python 3.10 或更高版本。
2. 复制根目录下的 `.env.example` 或自行设置环境变量。
3. 如需完整权限，先准备网站账号对应的 `NEUXSBOT_TOKEN`。

示例环境变量：

```env
NEUXSBOT_API_BASE_URL=https://www.neuxsbot.com
NEUXSBOT_TOKEN=
NEUXSBOT_PERIODS=100
```

## 依赖安装

部分脚本依赖 `numpy`、`pandas`：

```bash
pip install -r examples/python/requirements.txt
```

## 运行示例

在仓库根目录执行：

```bash
python examples/python/fc3d_markov/main.py --periods 120
python examples/python/ssq_quantum/main.py --periods 120
python examples/python/dlt_hybrid/main.py --periods 120
python examples/python/kl8_frequency/main.py --periods 120
```

Windows 用户也可以直接运行对应目录下的 `run.bat`。

## 适合什么场景

- 本地直接跑分析脚本
- 验证算法思路
- 基于现有脚本继续改造
- 后续自己打包成 EXE

## 注意事项

- 这些脚本会联网访问 `https://www.neuxsbot.com/api/v1/mcp/lottery/*`
- 部分接口需要有效 Token 才能读取完整数据
- 如果出现 `HTTP 429`，通常表示请求频率过高或账号额度触发限制
- 这些脚本属于本地分析程序，不是正式的 AI 对话入口

如果你要接入 Claude Desktop、Cursor、VS Code 等 AI 工具，请改用仓库里的 `nbcp` / MCP 接入方式。
