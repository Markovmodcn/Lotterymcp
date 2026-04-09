# MCP 接入说明

这份文档只讲一件事：怎么把 Lotterymcp 接到支持 MCP 的 AI 工具里，并让它正常读取网站历史开奖数据。

## 接入前先准备

1. 注册或登录 [NEUXSBOT 官网](https://www.neuxsbot.com)。
2. 进入 [个人中心](https://www.neuxsbot.com/member) 确认账号状态。
3. 在个人中心复制你的 MCP 密钥。
4. 确认本机已经安装 Node.js 20 或更高版本。

## 适合接入到哪些工具

当前最适合的场景：

- Claude Desktop
- Cursor
- VS Code
- 其他支持 MCP `stdio` 的桌面 AI 工具

仓库里已经提供了现成样例：

- `examples/claude-desktop.json`
- `examples/generic-mcp.json`

## 方式一：先用中文菜单配置

第一次接入，建议先走这个流程。

启动菜单：

```bash
npx --yes lotterymcp@latest
```

或者：

```bash
lotterymcp
```

菜单里主要做 4 件事：

1. 查看密钥获取入口。
2. 保存接口地址、密钥、默认分析期数。
3. 生成 MCP 配置片段。
4. 检查当前配置和接口连通性。

正常顺序就是先拿密钥，再保存配置，再生成配置片段，最后贴进 AI 工具。

## 方式二：直接写 MCP 配置

如果你已经知道怎么配置 MCP，可以直接把下面内容填进客户端：

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

如果已经全局安装，则可以改成：

```json
{
  "mcpServers": {
    "neuxsbot-cp": {
      "command": "lotterymcp",
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

## 环境变量说明

- `NEUXSBOT_API_BASE_URL`：接口基地址，默认使用 `https://www.neuxsbot.com`
- `NEUXSBOT_TOKEN`：网站账号对应的真实密钥，必须填写
- `NEUXSBOT_DEFAULT_PERIODS`：默认分析期数，AI 对话里仍然可以临时覆盖
- `NBCP_CONFIG_PATH`：可选，本地配置文件路径

## 接好以后怎么用

你不需要在本地把彩种写死，也不需要每次手工查开奖。

在 AI 对话里直接说需求就行，例如：

- 帮我分析最近 100 期福彩 3D 的冷热号和跨度。
- 读取最近 120 期双色球历史数据，按红球三区和蓝球热度做总结。
- 帮我读取最近 150 期快乐 8，再按分区和遗漏情况做汇总。
- 结合我最近的购买记录，分析我的选号偏好。

## 实际调用链路

真实使用流程是这样的：

1. 网站提供历史开奖数据接口。
2. 网站账号体系负责密钥和权限状态。
3. 本地 MCP 通过 `stdio` 把数据能力接进 AI 工具。
4. AI 在对话里动态选择彩种、期数和分析方向。

所以官网、账号状态和 MCP 密钥不是额外步骤，而是整个使用链路的一部分。

## 常见问题

### 1. 返回 401 或 403

通常是密钥无效、已撤销，或当前账号没有对应权限。先回网站检查账号状态，再重新获取密钥。

### 2. 返回 429

通常表示当前请求频率过高，或者账号额度触发限制。先减少请求频率和分析期数，再重新尝试。

### 3. AI 客户端没有触发工具

先确认三件事：

- 当前客户端真的支持 MCP `stdio`
- MCP 配置已经保存成功
- 启动命令还是 `lotterymcp@latest serve` 或 `lotterymcp serve`

### 4. 不接模型能不能用

可以。仓库里的 Python 分析程序可以直接联网读取历史数据，然后在本地计算。

## 建议排查顺序

1. 运行 `lotterymcp doctor`
2. 检查 `NEUXSBOT_API_BASE_URL` 是否仍为 `https://www.neuxsbot.com`
3. 检查密钥是否复制完整
4. 检查网站账号状态是否正常
5. 再确认 AI 工具是否已经真正加载 MCP 配置
