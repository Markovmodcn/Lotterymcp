# Lotterymcp Windows 便携版

这个目录用于说明 `nbcp.exe` 便携版的使用方式。

它适合不想额外安装 Node.js、希望在 Windows 上直接双击或命令行运行的人。对外使用逻辑与 `npx --yes lotterymcp@latest` 保持一致。

## 包含内容

- `nbcp.exe`：Windows 可执行文件，支持 `init`、`doctor`、`login`、`serve`、`analyze` 等命令
- `cp.config.json`：首次执行 `init` 后生成的本地配置文件
- 本说明文档：便携版接入说明

## 使用前准备

1. 确保本机可以访问 [https://www.neuxsbot.com](https://www.neuxsbot.com)
2. 先注册或登录网站账号
3. 在个人中心复制你的 MCP 密钥

## 快速开始

### 1. 初始化本地配置

```powershell
.\nbcp.exe init
```

按提示填入：

- 接口地址：默认 `https://www.neuxsbot.com`
- MCP 密钥：网站账号对应的真实密钥
- 默认分析期数：例如 `100`

### 2. 诊断接口连通性

```powershell
.\nbcp.exe doctor
```

这个命令会读取本地配置，并检查当前接口、密钥和工具能力是否可用。

### 3. 启动 MCP 服务

```powershell
.\nbcp.exe serve
```

启动后保持窗口运行，等待 Claude Desktop、Cursor、VS Code 等 MCP 客户端通过 `stdio` 连接。

## MCP 配置示例

```json
{
  "mcpServers": {
    "neuxsbot-cp": {
      "command": "C:\\Tools\\nbcp.exe",
      "args": ["serve"],
      "env": {
        "NEUXSBOT_API_BASE_URL": "https://www.neuxsbot.com",
        "NEUXSBOT_TOKEN": "your-real-token",
        "NEUXSBOT_DEFAULT_PERIODS": "100"
      }
    }
  }
}
```

## 常用命令

- `.\nbcp.exe`：打开中文菜单
- `.\nbcp.exe init`：保存接口地址、密钥和默认分析期数
- `.\nbcp.exe doctor`：检查配置和接口连通性
- `.\nbcp.exe login`：输出官网与账号入口
- `.\nbcp.exe serve`：启动 MCP `stdio` 服务
- `.\nbcp.exe analyze fc3d --periods 120`：直接运行本地分析程序

## 常见问题

### 1. 返回 401 或 403

通常表示密钥无效、已失效，或当前账号没有对应权限。先回网站个人中心检查账号状态和密钥。

### 2. 返回 429

通常表示请求频率过高，或者账号额度触发限制。先降低分析期数和请求频率，再重新尝试。

### 3. AI 工具没有触发 MCP

先确认三件事：

- 当前客户端真的支持 MCP `stdio`
- MCP 配置已经保存成功
- `command` 和 `args` 指向了实际可执行的 `nbcp.exe serve`

## 说明

- 便携版只是本地接入层，不包含网站后台和数据采集系统
- 彩种和期数不需要在本地写死，可以在 AI 对话里动态指定
- 账号权限、调用次数和真实数据都由网站账号体系控制
