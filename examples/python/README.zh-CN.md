# Lotterymcp Python ??????

这一组示例用于展示另一条使用路径：

- `MCP`：适合 Claude、Cursor、VS Code、桌面端等 AI 工具
- `Python 分析程序`：适合本地联网取数后直接做算法分析，不依赖大模型

## 核心特点

- 需要联网访问 `https://www.neuxsbot.com/api/v1/mcp/lottery/*`
- 不需要接模型
- 可以带 `NEUXSBOT_TOKEN`，也可以先使用公开数据范围
- 每个脚本都支持 `--periods` 和 `--output`
- 输出既会打印到终端，也会写入 JSON 文件

## 当前示例

- `fc3d_markov`：福彩3D分析程序
- `pl3_markov`：排列3分析程序
- `ssq_quantum`：双色球全匹配深度分析程序
- `dlt_hybrid`：大乐透反推分析程序
- `pailie5_positional`：排列5位置趋势分析程序
- `select7_positional`：七星彩位置趋势分析程序
- `kl8_frequency`：快乐8频率遗漏分析程序

## 环境变量

可复制根目录下的 `.env.example`：

```env
NEUXSBOT_API_BASE_URL=https://www.neuxsbot.com
NEUXSBOT_TOKEN=
NEUXSBOT_PERIODS=100
```

## 依赖安装

福彩3D / 排列3 的原版分析脚本依赖 `numpy` 和 `pandas`，首次运行前建议先安装：

```bash
pip install -r examples/python/requirements.txt
```

## 运行方式

从仓库根目录运行，例如：

```bash
python examples/python/fc3d_markov/main.py --periods 120
python examples/python/ssq_quantum/main.py --periods 120
python examples/python/dlt_hybrid/main.py --periods 120
python examples/python/kl8_frequency/main.py --periods 120
```

其中 `dlt_hybrid` 的输出 JSON 现已带上 `validation` 回测摘要，可直接查看回测样本数、平均命中、命中分布和最近回测样例。

如果命令行提示 `HTTP 429`，说明当前接口请求过于频繁。优先检查是否已经配置 `NEUXSBOT_TOKEN`，并适当降低连续调用频率后再重试。

Windows 用户也可以直接运行对应目录下的 `run.bat`。

## 说明边界

- 这些脚本属于“本地分析程序”，不是正式的 AI 对话入口
- 正式接入 AI 工具请使用仓库中的 `nbcp` / MCP 服务
- 这些脚本用于演示、研究、二次开发和后续 EXE 打包基础

