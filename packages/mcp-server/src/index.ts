import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js'
import {
  LOTTERY_MCP_TOOLS,
  McpApiError,
  createLotteryMcpClient,
  formatMcpApiError,
  type LotteryMcpClientConfig,
} from '@nexusbot/lottery-mcp-core'
import { z } from 'zod'

export const MCP_SERVER_TRANSPORT = 'stdio'
export const MCP_SERVER_TOOLS = [...LOTTERY_MCP_TOOLS]

type LotteryMcpClientLike = {
  getLatest: (input: { lotteryType: string }) => Promise<any>
  getHistory: (input: {
    lotteryType?: string
    period?: string
    fromDate?: string
    toDate?: string
    page?: number
    limit?: number
  }) => Promise<any>
  getPeriods: (input: {
    lotteryType: string
    page?: number
    limit?: number
  }) => Promise<any>
  getSummary: (input: { lotteryType?: string }) => Promise<any>
}

export type LotteryToolDefinition = {
  name: string
  description: string
  inputSchema: Record<string, z.ZodTypeAny>
  handler: (args: Record<string, unknown>) => Promise<CallToolResult>
}

const DEFAULT_PERIODS = 100

const normalizeDefaultPeriods = (value: unknown) => {
  const parsed = Number(String(value || '').trim())
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : DEFAULT_PERIODS
}

const serializeToolPayload = (payload: unknown) => JSON.stringify(payload, null, 2)

const createSuccessResult = (payload: unknown): CallToolResult => ({
  isError: false,
  content: [{ type: 'text', text: serializeToolPayload(payload) }],
  structuredContent: payload as Record<string, unknown>,
})

const createErrorResult = (error: unknown): CallToolResult => {
  if (error instanceof McpApiError) {
    return {
      isError: true,
      content: [{ type: 'text', text: formatMcpApiError(error) }],
      structuredContent: {
        statusCode: error.statusCode,
        code: error.code,
        message: error.message,
        upgradeUrl: error.upgradeUrl,
        displayMode: error.displayMode,
        action: error.action,
      },
    }
  }

  const message = error instanceof Error ? error.message : String(error)
  return {
    isError: true,
    content: [{ type: 'text', text: `调用失败: ${message}` }],
  }
}

const withToolExecution = async (callback: () => Promise<unknown>) => {
  try {
    return createSuccessResult(await callback())
  } catch (error) {
    return createErrorResult(error)
  }
}

export const createLotteryToolCatalog = (
  client: LotteryMcpClientLike,
  options?: { defaultPeriods?: number | string },
): LotteryToolDefinition[] => {
  const fallbackLimit = normalizeDefaultPeriods(options?.defaultPeriods)

  return [
    {
      name: 'lottery.latest',
      description: '获取指定彩种的最新开奖数据。',
      inputSchema: {
        lotteryType: z.string().min(1).describe('彩种代码，例如 fc3d、ssq、dlt。'),
      },
      handler: async (args) =>
        withToolExecution(() =>
          client.getLatest({ lotteryType: String(args.lotteryType || '').trim() })),
    },
    {
      name: 'lottery.history',
      description: '查询历史开奖列表，未传 limit 时默认使用本地配置期数。',
      inputSchema: {
        lotteryType: z.string().optional().describe('可选。彩种代码，例如 fc3d、ssq、dlt。'),
        period: z.string().optional().describe('可选。按期号筛选。'),
        fromDate: z.string().optional().describe('可选。开始日期，格式 YYYY-MM-DD。'),
        toDate: z.string().optional().describe('可选。结束日期，格式 YYYY-MM-DD。'),
        page: z.number().int().positive().optional().describe('可选。分页页码。'),
        limit: z.number().int().positive().optional().describe('可选。返回条数。'),
      },
      handler: async (args) =>
        withToolExecution(() =>
          client.getHistory({
            lotteryType: typeof args.lotteryType === 'string' ? args.lotteryType : undefined,
            period: typeof args.period === 'string' ? args.period : undefined,
            fromDate: typeof args.fromDate === 'string' ? args.fromDate : undefined,
            toDate: typeof args.toDate === 'string' ? args.toDate : undefined,
            page: typeof args.page === 'number' ? args.page : undefined,
            limit: typeof args.limit === 'number' ? args.limit : fallbackLimit,
          })),
    },
    {
      name: 'lottery.periods',
      description: '列出某个彩种的历史期号列表。',
      inputSchema: {
        lotteryType: z.string().min(1).describe('彩种代码，例如 fc3d、ssq、dlt。'),
        page: z.number().int().positive().optional().describe('可选。分页页码。'),
        limit: z.number().int().positive().optional().describe('可选。返回条数。'),
      },
      handler: async (args) =>
        withToolExecution(() =>
          client.getPeriods({
            lotteryType: String(args.lotteryType || '').trim(),
            page: typeof args.page === 'number' ? args.page : undefined,
            limit: typeof args.limit === 'number' ? args.limit : fallbackLimit,
          })),
    },
    {
      name: 'lottery.summary',
      description: '查看单个彩种或全部可用彩种的数据摘要。',
      inputSchema: {
        lotteryType: z.string().optional().describe('可选。彩种代码，例如 fc3d、ssq、dlt。'),
      },
      handler: async (args) =>
        withToolExecution(() =>
          client.getSummary({
            lotteryType: typeof args.lotteryType === 'string' ? args.lotteryType : undefined,
          })),
    },
  ]
}

export const createLotteryMcpServer = (options: LotteryMcpClientConfig) => {
  const client = createLotteryMcpClient(options)
  const server = new McpServer({
    name: 'neuxsbot-lottery-mcp',
    version: '0.1.0',
  })

  const toolCatalog = createLotteryToolCatalog(client, {
    defaultPeriods: options.defaultPeriods,
  })

  toolCatalog.forEach((tool) => {
    server.registerTool(
      tool.name,
      {
        description: tool.description,
        inputSchema: tool.inputSchema,
      },
      async (args) => tool.handler(args as Record<string, unknown>),
    )
  })

  return {
    client,
    server,
    toolCatalog,
  }
}

export const startLotteryMcpStdioServer = async (options: LotteryMcpClientConfig) => {
  const { client, server, toolCatalog } = createLotteryMcpServer(options)
  const transport = new StdioServerTransport()
  await server.connect(transport)

  return {
    client,
    server,
    toolCatalog,
    transport,
  }
}

export const startNbcpStdioServer = startLotteryMcpStdioServer
