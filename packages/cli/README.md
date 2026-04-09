# Lotterymcp

`neuxnbcp` 是面向 NEUXSBOT 彩票数据服务的公开 MCP 命令行入口包。

它提供两种用法：

- 直接运行中文初始化菜单
- 作为 MCP `stdio` 服务接入 Claude Desktop、Cursor、VS Code 或其他支持 MCP 的工具

如果你只是临时试用，直接跑 `npx --yes neuxnbcp@latest`。
如果你准备长期使用，安装后直接运行 `nbcp`。

## 快速开始

直接运行：

```bash
npx --yes neuxnbcp@latest
```

全局安装：

```bash
npm i -g neuxnbcp
nbcp
```

## 你需要先准备

1. 打开 [https://www.neuxsbot.com](https://www.neuxsbot.com)
2. 注册或登录
3. 打开官网账号页 [https://www.neuxsbot.com/member](https://www.neuxsbot.com/member)
4. 在密钥页获取 MCP Token：
   [https://www.neuxsbot.com/member/api-keys](https://www.neuxsbot.com/member/api-keys)

## 常用命令

```bash
nbcp
nbcp init
nbcp doctor
nbcp login
nbcp serve
```

- `nbcp`: 打开中文菜单
- `nbcp init`: 保存接口地址、Token、默认期数
- `nbcp doctor`: 检查当前配置和网站连通性
- `nbcp login`: 输出官网、账号页和密钥页链接
- `nbcp serve`: 启动真正的 MCP `stdio` 服务

## 连通性提示

- `nbcp doctor` 会直接请求网站健康接口，验证当前 API 地址、Token 和工具列表是否可用。
- 如果命令行提示 `HTTP 429`，说明当前 Token 配额或请求频率触发限制。先降低默认期数、减少连续请求，再回官网账号页检查当前状态。

## MCP 配置示例

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

## 说明

- 彩种不在本地写死，由 AI 对话动态传入
- Token 权限、调用次数、账号状态由 NEUXSBOT 网站控制
- 这个 npm 包只公开客户端和 MCP 代理层，不包含网站后端和数据采集系统
- 完整示例、Python 本地分析程序和 AI 提示词模板请以 GitHub 仓库主页说明为准
