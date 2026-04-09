# Lotterymcp ???

????? Lotterymcp ????????????? NEUXSBOT ???????? AI ??????????? `NEUXSBOT_TOKEN` ???? [www.neuxsbot.com](https://www.neuxsbot.com) ??????????????????????????? EXE ????? CLI?????MCP ??????????

快速入口：

- GitHub 快速上手：[docs/github-quickstart.zh-CN.md](docs/github-quickstart.zh-CN.md)
- Lotterymcp ?????[docs/mcp-usage.zh-CN.md](docs/mcp-usage.zh-CN.md)
- AI 提示词模板：[docs/prompt-templates.zh-CN.md](docs/prompt-templates.zh-CN.md)
- Python 本地分析程序：[examples/python/README.zh-CN.md](examples/python/README.zh-CN.md)

## 目录说明

### 包含

- `packages/cli`：提供 `npx --yes neuxnbcp@latest` 临时运行入口，安装后可直接使用 `nbcp` 命令；内置注册/配置/诊断/启动流程。
- `packages/core`：MCP 客户端逻辑，封装 `/api/v1/mcp/*` 请求、认证、错误规范等。
- `packages/mcp-server`：本地 `stdio` 代理服务，向上游暴露 `lottery.latest`、`lottery.history`、`lottery.periods`、`lottery.summary` 工具并转发请求到网站接口。
- `examples/`：Claude Desktop / 通用 MCP 配置样例，以及 7 个彩种的 Python 本地分析程序示例。
- `docs/`：设计、计划和发布说明（不包含私有数据源）。

### 不包含

- NEUXSBOT 网站源码、账号后台、数据采集或桌面 UI。
- 私有 API 的源代码和加密密钥。
- 与官网部署/统计相关的后台逻辑。

## 支持的工具

- `lottery.latest`
- `lottery.history`
- `lottery.periods`
- `lottery.summary`

## 快速上手

1. **注册并获取 Token**
   - 打开 [https://www.neuxsbot.com](https://www.neuxsbot.com)，注册或登录。
   - 打开官网账号页：[https://www.neuxsbot.com/member](https://www.neuxsbot.com/member)。
   - 在密钥页复制 MCP Token：[https://www.neuxsbot.com/member/api-keys](https://www.neuxsbot.com/member/api-keys)。

2. **启动中文菜单**

```bash
npx --yes neuxnbcp@latest
```

   - 选项 1 会展示 Token 页面说明；选项 2 可以输入接口地址、Token、默认期数；选项 3 生成 MCP 配置片段并复制给支持 MCP 的 AI 工具；选项 4 检查当前配置和网站连通性；选项 5 启动本地服务。

3. **配置本地参数 / `nbcp init`**

```bash
npx --yes neuxnbcp@latest init
```

   - `API_BASE_URL`: 设置为 `https://www.neuxsbot.com` 或你的代理地址。
   - `TOKEN`: 填写从官网密钥页获取的 MCP Token。
   - `DEFAULT_PERIODS`: 合理的默认期数（例如 `100`），AI 工具可在对话中覆盖。
   - `NBCP_CONFIG_PATH`（可选）：默认 `~/.nbcp/cp.config.json`，你可以设置为其他路径用于多配置环境。

4. **健康检查**

```bash
npx --yes neuxnbcp@latest doctor
```

   - 会读取已有配置，调用 `/api/v1/mcp/health`，输出服务名称、传输方式、当前工具列表等，验证 Token/接口是否可达。
   - 如果这里提示 `HTTP 429`，说明当前请求频率或账号配额触发限制，建议稍后重试，并先降低默认期数或连续调用频率。

5. **启动 MCP stdio 服务**

```bash
npx --yes neuxnbcp@latest serve
```

   - 启动后 MCP 服务持续运行，AI 工具有权限调用 `lottery.*` 工具并由本地 `stdio` 代理转发至 NEUXSBOT 网站。

如果你想看完整接入链路、AI 工具适配范围、官网账号页和密钥页说明，直接看：

- [docs/mcp-usage.zh-CN.md](docs/mcp-usage.zh-CN.md)

## 安装方式

临时运行：

```bash
npx --yes neuxnbcp@latest
```

全局安装后直接用：

```bash
npm i -g neuxnbcp
nbcp
```

如果你只是首次试用，用 `npx` 即可。
如果你需要长期使用或反复改配置，直接全局安装更省事。

## 接入后用户实际能做什么

- 在 AI 对话里动态切换福彩3D、排列3、双色球、大乐透、排列5、七星彩、快乐8
- 按不同期数读取历史开奖
- 让 AI 基于历史数据做热号、冷号、和值、跨度、位置、分区等分析
- 结合你自己的购买记录一起分析
- 在不接模型的情况下，直接运行仓库里的 Python 本地分析程序

如果你是第一次接触这个项目，可以把它理解成：

- 官网负责账号、Token、权限状态和真实数据接口
- MCP 负责把这些数据接进 AI 工具
- AI 负责把历史数据转成你能直接看的分析结果

官网入口：

- 官网首页：[https://www.neuxsbot.com](https://www.neuxsbot.com)
- 官网账号页：[https://www.neuxsbot.com/member](https://www.neuxsbot.com/member)
- MCP 密钥页面：[https://www.neuxsbot.com/member/api-keys](https://www.neuxsbot.com/member/api-keys)

## Python 本地分析程序

除了 MCP 接入方式，本仓库还提供一组“联网取数 + 本地分析”的 Python 示例，适合：

- 想直接跑算法脚本的用户
- 想二次开发彩票分析逻辑的开发者
- 想后续打包成 EXE 的场景

这组脚本：

- 通过 `https://www.neuxsbot.com/api/v1/mcp/lottery/*` 拉取历史数据
- 不依赖大模型
- 支持命令行参数 `--periods` 和 `--output`
- 每个彩种都有独立目录和 `run.bat`
- 福彩3D / 排列3 原版脚本需先安装 `examples/python/requirements.txt` 中的 `numpy`、`pandas`
- 如果命令行提示 `HTTP 429`，说明当前接口请求过于频繁，优先检查 `NEUXSBOT_TOKEN` 是否已配置，并降低连续调用频率后再重试

当前示例目录：

- `examples/python/fc3d_markov`：福彩3D逆向分析程序
- `examples/python/pl3_markov`：排列3逆向分析程序
- `examples/python/ssq_quantum`：双色球全匹配深度分析程序
- `examples/python/dlt_hybrid`：大乐透反推分析程序
- `examples/python/pailie5_positional`：排列5位置趋势分析程序
- `examples/python/select7_positional`：七星彩位置趋势分析程序
- `examples/python/kl8_frequency`：快乐8频率遗漏分析程序

总说明见：

- [examples/python/README.zh-CN.md](examples/python/README.zh-CN.md)
- [docs/github-quickstart.zh-CN.md](docs/github-quickstart.zh-CN.md)
- [docs/mcp-usage.zh-CN.md](docs/mcp-usage.zh-CN.md)
- [docs/prompt-templates.zh-CN.md](docs/prompt-templates.zh-CN.md)

示例运行方式：

```bash
python examples/python/fc3d_markov/main.py --periods 120
python examples/python/ssq_quantum/main.py --periods 120
python examples/python/dlt_hybrid/main.py --periods 120
python examples/python/kl8_frequency/main.py --periods 120
```

大乐透示例的 JSON 输出现已包含 `validation` 回测摘要，包含回测样本数、平均前后区命中、命中分布和最近回测样例。

## CLI 命令参考

- `nbcp`：不带参数运行交互菜单，适合初次接入的用户。
- `nbcp init`：交互式输入 API 地址、Token、默认期数，并写入本地配置。
- `nbcp doctor`：检查当前配置和网站连通性，请求 `/api/v1/mcp/health`，并把遗漏项打印出来。
- `nbcp login`：输出官网、账号页和密钥页链接，方便用户快速跳转获取 Token。
- `nbcp serve`：启动 `stdio` 代理服务，需先通过 `init`/菜单完成配置。

## 配置说明

1. `NEUXSBOT_API_BASE_URL`：请求基址，默认 `https://www.neuxsbot.com`。
2. `NEUXSBOT_TOKEN`：MCP Token，必须填写。
3. `NEUXSBOT_DEFAULT_PERIODS`：默认期数，AI 对话可自由覆盖。
4. `NBCP_CONFIG_PATH`：可选配置文件路径，未设置时默认 `~/.nbcp/cp.config.json`。

配置会存储为 JSON 结构：

```json
{
  "apiBaseUrl": "<YOUR_URL>",
  "token": "<YOUR_TOKEN>",
  "defaultPeriods": "100"
}
```

环境变量优先级高于配置文件，`init` 命令会改写配置文件。

## 常见问题与故障排查

### Token 无效

- 原因：输入错误、账号权限不足，或 Token 过期/撤销。
- 处理：重新登录官网账号页，复制新的 MCP Token；确认终端没有隐藏字符；再运行 `nbcp init`。

### 每日/每月配额

- Token 会携带账号配额限制（每日调用数、并发、最大期数）。超过后接口返回 429。
- 处理：调整调用频率、降低默认期数，或回官网账号页查看当前可用状态：[https://www.neuxsbot.com/member](https://www.neuxsbot.com/member)。

### 账号状态异常

- 官网返回 `403`/`membership expired` 时说明当前账号暂无访问权限。
- 处理：登录 NEUXSBOT 网站查看账号状态；如果仍然报错，检查是否在官网密钥页生成了正确的 Token。

## 开发与贡献

- 安装依赖：`npm install`
- 构建：`npm run build`
- 运行测试：`npm test`
- Python 示例测试：`python -m unittest discover -s tests/python`
- 如果改动了 `examples/python/` 或 `common/` 下的分析逻辑，提交前至少跑一次 Node 构建和 Python 单元测试。
- README 支持多语言说明，`packages/cli` 中的 `config.ts` 控制命令行文案，`packages/mcp-server` 列出工具定义。
- `examples/` 提供具体的 Claude Desktop 与通用 MCP 配置，`examples/python/` 提供本地分析程序示例。

## 项目结构

```
nexusbot-lottery-mcp/
  apps/               # 便携版打包
  docs/               # 计划和设计文档
  examples/           # Claude or generic MCP config samples
  packages/
    cli/
    core/
    mcp-server/
  tests/               # CLI、核心库、MCP 服务器的自动化
  README.md
  package.json
```

## 发布边界

本仓库仅发布 MCP 客户端/代理层，供其他 AI 工具通过 `stdio` 启动、配置 `NEUXSBOT_TOKEN` 直接接入。所有涉及官网部署、账号系统、数据采集和桌面 UI 的内容都托管在内网/其他仓库，不在此公开发行。

