# Lotterymcp Windows ???

????? `nbcp.exe` ????????????? Windows ????????? npm/Node.js ????????? Lotterymcp ?????? NEUXSBOT ?????????

## 包含内容

- `nbcp.exe`：经过打包的可执行文件，逻辑与 [`npx neuxnbcp`](https://www.npmjs.com/package/neuxnbcp) 保持一致，支持 `init`、`doctor`、`serve`、`login` 等命令。
- `cp.config.json`（可选）：便携版在首次运行 `init` 时会生成，保存当前的接口地址、Token 和默认期数。
- 简洁说明文档（本文件），与主 README 保持口径一致。

## 当前状态

- 当前仓库已经完成 npm CLI 版本，可直接使用：`npx --yes neuxnbcp@latest`
- `nbcp.exe` 绿色版说明先收录在这里，正式下载地址以实际发布页为准

## 准备工作

1. 从你的正式发布页或内部 release 解压 `nbcp.exe` 到任意目录。
2. 确保目标主机能访问外网 `https://www.neuxsbot.com`，便携版本依赖这个接口获取授权和最新工具列表。
3. 如果希望用 PowerShell 直接启动，建议把解压目录加入 `PATH` 或使用 `.\nbcp.exe` 形式调用。

## 快速启动流程

### 1. 先注册并获取 Token

1. 打开 [www.neuxsbot.com](https://www.neuxsbot.com)。
2. 登录后进入 [会员中心](https://www.neuxsbot.com/member)。
3. 在 [API Keys 页面](https://www.neuxsbot.com/member/api-keys) 复制 MCP Token。
4. Token 会自动关联会员组、调用次数和权限。免费组默认每日试用次数有限，付费组可以在后台控制每日调用量与并发数量。

### 2. 生成本地配置（只需执行一次）

```powershell
.\nbcp.exe init
```

按照提示依次填写接口地址（默认 `https://www.neuxsbot.com`）、Token、默认期数（例如 `100`）。CLI 会把值写入 `cp.config.json` 并输出当前配置摘要。

### 3. 检查与健康诊断

```powershell
.\nbcp.exe doctor
```

`doctor` 会读取本地配置，验证 API 是否能连通并输出 MCP 服务名、传输方式、工具列表（`lottery.latest` 等）以及当前签名所允许的鉴权头。
如果这里返回 `HTTP 429`，表示当前请求频率或账号配额触发限制，建议稍后重试，并先降低默认期数或连续调用频率。

### 4. 启动 MCP stdio 服务

```powershell
.\nbcp.exe serve
```

启动后维持在前台运行，等待 AI 工具（Claude Desktop、Cursor、任意支持 MCP 的客户端）通过 stdio 与 4 个工具交互：`lottery.latest`、`lottery.history`、`lottery.periods`、`lottery.summary`。AI 侧可动态传入彩种、期数、统计维度，客户端不再写死彩种。

## Windows 集成示例

如果你要在其他 MCP 客户端中引用这个便携版，请将 `{path}` 替换为实际路径，示例如下：

```json
{
  "mcpServers": {
    "neuxsbot-cp": {
      "command": "C:\\\\Tools\\\\nbcp.exe",
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

便携版会使用环境变量优先级，`init` 所写入的值仅作为默认值。若你希望在命令行或脚本中覆盖，每次启动前设置以下变量即可：

```powershell
$env:NEUXSBOT_TOKEN = 'xxx'
$env:NEUXSBOT_DEFAULT_PERIODS = '200'
.\nbcp.exe serve
```

## CLI 命令速览

- `.\nbcp.exe`：启动交互菜单，显示 `注册/登录`、`配置`、`复制 MCP 配置片段`、`检查当前配置和网站连通性`、`启动服务`等选项（中文提示，兼容非交互环境自动回退）。
- `.\nbcp.exe init`：按提示保存 API 地址、Token、默认期数到本地配置。
- `.\nbcp.exe doctor`：进行一次真实健康检查并输出连接详细信息。
- `.\nbcp.exe login`：直接打印网站、会员中心、Token 页面链接，方便复制到浏览器。
- `.\nbcp.exe serve`：保持 MCP stdio 通道，等待 AI 工具连接，建议配合 `powershell -NoProfile -Command` 执行。

## 常见问题

- **扫码能连通但 `serve` 报 `未检测到完整配置`？**  
  先用 `init` 完成填写或检查环境变量是否为空；`doctor` 会列出缺失项。
- **`doctor` / `serve` 提示 `HTTP 429`？**  
  说明当前请求频率或账号配额触发限制。先降低默认期数、减少连续请求，再去 [https://www.neuxsbot.com/member/api-keys](https://www.neuxsbot.com/member/api-keys) 检查密钥状态。
- **Token 用完了怎么办？**  
  进入会员中心 [https://www.neuxsbot.com/member/api-keys](https://www.neuxsbot.com/member/api-keys) 生成新密钥，或者升级会员组增加每日调用额度。
- **想让便携版陪跑多个 AI 工具？**  
 每次 `serve` 只能维持一个 stdio 会话，若需要并发请参考成员服务器部署或在多个目录分别运行 `nbcp.exe serve`，环境变量确保不冲突。

## 备注

本便携版为了保持安全，默认不会写入敏感信息到系统路径；所有配置存储在与 `nbcp.exe` 同级的 `cp.config.json`（可替换）并可以通过环境变量或命令参数覆盖。任何需要对接的 AI 工具都只需通过标准 MCP 协议访问 `lottery.*` 工具即可。
