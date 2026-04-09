# Lotterymcp CLI

`neuxnbcp` 是 Lotterymcp 的实际 CLI 实现包。

普通用户直接使用对外短命令包 `lotterymcp` 即可。

它负责两件事：

- 提供中文菜单，帮助用户完成本地配置
- 以 MCP `stdio` 服务形式接入支持 MCP 的 AI 工具

## 安装

临时运行：

```bash
npx --yes lotterymcp@latest
```

全局安装：

```bash
npm i -g lotterymcp
lotterymcp
```

## 常用命令

```bash
lotterymcp
lotterymcp init
lotterymcp doctor
lotterymcp login
lotterymcp serve
lotterymcp analyze fc3d --periods 120
```

- `lotterymcp`：打开中文菜单
- `lotterymcp init`：保存接口地址、密钥和默认分析期数
- `lotterymcp doctor`：检查当前配置和接口连通性
- `lotterymcp login`：输出官网和账号入口
- `lotterymcp serve`：启动 MCP `stdio` 服务
- `lotterymcp analyze`：直接运行本地分析程序

## 使用前准备

1. 打开 [https://www.neuxsbot.com](https://www.neuxsbot.com)
2. 注册或登录账号
3. 在个人中心复制你的 MCP 密钥

## MCP 配置示例

```json
{
  "mcpServers": {
    "neuxsbot-cp": {
      "command": "npx",
      "args": ["-y", "lotterymcp@latest", "serve"],
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

- 彩种和期数不需要在本地写死，可以在 AI 对话中动态指定
- 密钥、调用次数和权限状态由网站账号体系控制
- 这个 npm 包只公开命令行接入层和本地 MCP 代理能力
- 完整使用说明请以仓库首页文档为准
