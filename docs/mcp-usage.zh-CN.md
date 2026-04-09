# Lotterymcp ????

??????????`Lotterymcp`??????? `neuxnbcp` / `nbcp`??????????????

## Lotterymcp ?????

它本质上是一个本地 `stdio` 中间层。

上游 AI 工具通过 MCP 调用：

- `lottery.latest`
- `lottery.history`
- `lottery.periods`
- `lottery.summary`

本地代理再把请求转发到：

- [NEUXSBOT 官网](https://www.neuxsbot.com)

也就是说：

- 历史数据来自官网接口
- Token 权限由官网账号系统控制
- 本地不写死彩种
- 彩种、期数、分析方向都由 AI 对话动态决定

## 适合接到哪些工具

当前最适合的场景：

- Claude Desktop
- Cursor
- VS Code
- 其他支持 MCP `stdio` 的桌面 AI 工具

仓库里已经放了配置样例：

- `examples/claude-desktop.json`
- `examples/generic-mcp.json`

## 使用前先做什么

1. 打开 [官网首页](https://www.neuxsbot.com)
2. 注册或登录账号
3. 打开 [官网账号页](https://www.neuxsbot.com/member)
4. 到 [MCP 密钥页](https://www.neuxsbot.com/member/api-keys) 复制 Token

为什么一定要先注册：

- Token 要用来识别你的权限
- 调用额度、可访问范围、期数限制都跟账号绑定
- 如遇权限或配额变化，也是在官网账号页查看当前状态
- 如果命令行提示 `HTTP 429`，通常表示当前调用过于频繁或额度已触发限制，优先回官网账号页确认状态，并降低默认 `periods` 或调用频率后再试

## 接入方式

### 方式一：临时运行

```bash
npx --yes neuxnbcp@latest
```

适合：

- 第一次试用
- 临时电脑
- 不想全局安装

### 方式二：长期使用

```bash
npm i -g neuxnbcp
nbcp
```

适合：

- 长期反复使用
- 经常切换 Token 或默认期数
- 同时接多个 AI 工具

### 方式三：直接写 MCP 配置

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

如果你已经全局安装，也可以改成：

```json
{
  "mcpServers": {
    "neuxsbot-cp": {
      "command": "nbcp",
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

## 中文菜单怎么用

运行：

```bash
nbcp
```

或：

```bash
npx --yes neuxnbcp@latest
```

菜单的作用：

1. 注册/登录并获取 Token
2. 配置接口地址、Token、默认期数
3. 生成 MCP 配置片段
4. 查看当前配置和连通性
5. 启动 MCP 服务

如果只是第一次接入，正常顺序就是：

1. 先拿 Token
2. 再保存配置
3. 再生成配置片段
4. 贴进 AI 工具
5. 最后让 AI 开始调用

## AI 对话里怎么触发

你不需要告诉 AI 去调用哪个本地文件。
你只需要自然说需求。

例如：

- 帮我分析最近 100 期福彩3D 的热号、冷号、和值和跨度
- 读取最近 120 期双色球历史数据，按红球三区、蓝球热度和重号趋势给我总结
- 帮我读取最近 100 期大乐透，前区后区分开分析
- 结合我最近 20 次购买记录，再读取最近 120 期开奖，分析我的选号偏好

更完整模板见：

- `docs/prompt-templates.zh-CN.md`

## 为什么官网链接要放进说明里

因为这个 MCP 不是离线玩具。

它的真实使用链路是：

1. 在官网注册
2. 在官网账号页生成 Token
3. 在 AI 工具里接入 MCP
4. 在对话中调用官网历史数据
5. 权限不足时回官网查看账号状态

所以官网、账号页、密钥页不是“广告外链”，而是整个使用流程的一部分。

## 免费与权限怎么理解

公开仓库不写死账号规则。

但用户需要知道这几点：

- 免费或试用账号也可以先接起来测试
- 实际调用次数、可分析期数、可访问范围以官网账号页显示为准
- 如果返回权限不足、配额不足或状态异常，应该回官网查看
- 本地 MCP 配置结构不用改，只需要更新 Token 或检查账号状态

## 常见使用路径

### 路径一：AI 对话分析

最适合大多数用户。

流程：

1. 接好 MCP
2. 在 AI 对话里直接提问
3. 让 AI 动态选择彩种和期数

### 路径二：Python 本地分析程序

最适合开发者、二次开发、后续 EXE 打包。

流程：

1. 保留官网 Token
2. 本地 Python 脚本读取官网历史数据
3. 本地执行分析逻辑，不依赖模型

说明见：

- `examples/python/README.zh-CN.md`

## 出现这些情况怎么处理

### 没数据

- 先跑 `nbcp doctor`
- 确认 `NEUXSBOT_API_BASE_URL` 还是 `https://www.neuxsbot.com`
- 确认 Token 没有复制错

### 返回权限不足

- 去 [官网账号页](https://www.neuxsbot.com/member) 检查当前状态
- 必要时重新生成 MCP Token

### 返回配额不足

- 降低调用频率
- 减少默认期数
- 需要更高额度时，在官网账号页查看当前可用状态

### AI 工具没有触发

- 先检查这个工具是否支持 MCP `stdio`
- 再检查 MCP 配置是否真的保存成功
- 确认启动命令是 `neuxnbcp@latest serve` 或 `nbcp serve`
