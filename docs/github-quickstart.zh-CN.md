# Lotterymcp GitHub 快速开始

这份说明适合第一次接触仓库的人。

目标只有一个：最快把 Lotterymcp 接起来，并在 AI 对话里读到真实历史开奖数据。

## 你会得到什么

- 一个可以接到 MCP 客户端的本地命令行入口
- 一套可直接复制的 MCP 配置示例
- 一组可单独运行的 Python 分析程序
- 一份用户可直接复制的问题示例

## 最快上手

1. 先在 [NEUXSBOT 官网](https://www.neuxsbot.com) 注册或登录。
2. 在个人中心获取你的 Token。
3. 本机安装 Node.js 20 或更高版本。
4. 运行下面命令打开中文菜单：

```bash
npx --yes neuxnbcp@latest
```

5. 在菜单里填好接口地址、Token 和默认分析期数。
6. 生成 MCP 配置片段。
7. 复制到 Claude Desktop、Cursor、VS Code 或其他支持 MCP 的客户端。

## 如果你想长期使用

```bash
npm i -g neuxnbcp
nbcp
```

常用命令：

```bash
nbcp
nbcp init
nbcp doctor
nbcp serve
```

## 直接复制的 MCP 配置

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

## 接好以后怎么提问

- 帮我分析最近 100 期福彩 3D 的热号、冷号、和值和跨度。
- 读取最近 120 期双色球历史数据，按红球三区和蓝球热度做总结。
- 读取最近 150 期快乐 8，按分区、奇偶和遗漏情况做汇总。
- 结合我最近 20 次购买记录，再分析最近 120 期开奖数据。

更多示例见：[docs/prompt-templates.zh-CN.md](docs/prompt-templates.zh-CN.md)

## 不接模型能不能用

可以。仓库里还带了 7 个 Python 本地分析程序，能联网拉取历史数据后自行计算。

说明见：[examples/python/README.zh-CN.md](../examples/python/README.zh-CN.md)

## 建议你先看这两份

- [MCP 接入说明](docs/mcp-usage.zh-CN.md)
- [分析问题示例](docs/prompt-templates.zh-CN.md)
