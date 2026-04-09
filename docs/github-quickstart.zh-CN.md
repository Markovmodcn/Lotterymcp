# Lotterymcp GitHub ???????

这份文档只解释公开仓库的实际用途和最短接入路径。

## 这个仓库能做什么

- 把 NEUXSBOT 的彩票历史数据接到支持 MCP 的 AI 工具里
- 通过 `nbcp` 中文菜单完成本地配置
- 让 AI 在对话里动态选择彩种、期数、历史数据范围
- 直接运行 7 个 Python 本地分析程序，不接模型也能联网分析

## 你需要先准备

1. 注册或登录 [NEUXSBOT 官网](https://www.neuxsbot.com)
2. 打开 [官网账号页](https://www.neuxsbot.com/member)
3. 在 [MCP 密钥页](https://www.neuxsbot.com/member/api-keys) 复制 Token

## 方式一：先临时试用

不安装，直接运行：

```bash
npx --yes neuxnbcp@latest
```

进入菜单后按顺序做：

1. 查看 Token 获取地址
2. 填入接口地址、Token、默认期数
3. 生成 MCP 配置片段
4. 复制到你的 AI 工具

如果后面命令行出现 `HTTP 429`，说明当前调用过于频繁或账号额度已触发限制。优先回官网账号页查看当前状态，并适当降低默认期数或调用频率后再重试。

适合第一次试用和临时机器。

## 方式二：长期使用

全局安装：

```bash
npm i -g neuxnbcp
```

安装后直接用：

```bash
nbcp
nbcp init
nbcp doctor
nbcp serve
```

适合长期使用、反复调整配置、或者本地已经接了多个 AI 工具的场景。

## 方式三：直接接到 AI 工具

如果你不想先跑菜单，也可以直接把下面的 MCP 配置放进支持 MCP 的工具：

```json
{
  "mcpServers": {
    "neuxsbot-cp": {
      "command": "npx",
      "args": ["-y", "neuxnbcp@latest", "serve"],
      "env": {
        "NEUXSBOT_API_BASE_URL": "https://www.neuxsbot.com",
        "NEUXSBOT_TOKEN": "your-real-token",
        "NEUXSBOT_DEFAULT_PERIODS": "100"
      }
    }
  }
}
```

示例文件：

- `examples/claude-desktop.json`
- `examples/generic-mcp.json`

如果你已经全局安装，也可以把 `command` 改成 `nbcp`，`args` 改成 `["serve"]`。

## 接好以后能怎么用

你不需要在本地写死彩种。
AI 在对话里会动态调用：

- `lottery.latest`
- `lottery.history`
- `lottery.periods`
- `lottery.summary`

典型用法：

- 分析最近 100 期福彩3D热号、冷号、和值、跨度
- 读取最近 120 期双色球历史数据，输出重号和分区趋势
- 结合我自己的购买记录，对比最近 100 期开奖
- 在同一轮对话里切换成大乐透、排列5、快乐8继续分析

更完整的提问模板见：

- `docs/prompt-templates.zh-CN.md`
- `docs/mcp-usage.zh-CN.md`

## 为什么建议走官网注册

这个项目的真实链路不是“下个脚本离线跑完”。

更合理的理解是：

- 官网负责真实数据接口
- 官网账号页负责 Token 和权限状态
- MCP 负责把数据接进 AI 工具
- AI 负责基于历史数据给你分析结果

所以注册官网账号不是额外步骤，而是使用流程的一部分。

相关入口：

- 官网首页：[https://www.neuxsbot.com](https://www.neuxsbot.com)
- 官网账号页：[https://www.neuxsbot.com/member](https://www.neuxsbot.com/member)
- MCP 密钥页面：[https://www.neuxsbot.com/member/api-keys](https://www.neuxsbot.com/member/api-keys)

## 不接模型也能用吗

可以。

仓库还带了 7 个 Python 本地分析程序：

- 福彩3D分析程序
- 排列3分析程序
- 双色球全匹配深度分析程序
- 大乐透反推分析程序
- 排列5位置趋势分析程序
- 七星彩位置趋势分析程序
- 快乐8频率遗漏分析程序

说明文档见：

- `examples/python/README.zh-CN.md`

## 公开版边界

这个 GitHub 仓库只公开：

- CLI 中文菜单
- MCP 客户端与 `stdio` 代理
- Python 本地分析程序示例
- 配置样例和说明文档

不公开：

- 网站后端
- 账号系统
- 数据采集系统
- 桌面端源码

## 遇到问题先查什么

1. `nbcp doctor`
2. Token 是否复制完整
3. Token 是否还有对应的账号权限
4. `NEUXSBOT_API_BASE_URL` 是否仍为 `https://www.neuxsbot.com`
5. AI 工具是否真的支持 MCP `stdio`
6. 权限不足或额度不足时，是否已经回官网账号页查看当前状态
