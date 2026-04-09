import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { type LotteryMcpClientConfig } from '@nexusbot/lottery-mcp-core';
import { z } from 'zod';
export declare const MCP_SERVER_TRANSPORT = "stdio";
export declare const MCP_SERVER_TOOLS: ("lottery.latest" | "lottery.history" | "lottery.periods" | "lottery.summary")[];
type LotteryMcpClientLike = {
    getLatest: (input: {
        lotteryType: string;
    }) => Promise<any>;
    getHistory: (input: {
        lotteryType?: string;
        period?: string;
        fromDate?: string;
        toDate?: string;
        page?: number;
        limit?: number;
    }) => Promise<any>;
    getPeriods: (input: {
        lotteryType: string;
        page?: number;
        limit?: number;
    }) => Promise<any>;
    getSummary: (input: {
        lotteryType?: string;
    }) => Promise<any>;
};
export type LotteryToolDefinition = {
    name: string;
    description: string;
    inputSchema: Record<string, z.ZodTypeAny>;
    handler: (args: Record<string, unknown>) => Promise<CallToolResult>;
};
export declare const createLotteryToolCatalog: (client: LotteryMcpClientLike, options?: {
    defaultPeriods?: number | string;
}) => LotteryToolDefinition[];
export declare const createLotteryMcpServer: (options: LotteryMcpClientConfig) => {
    client: import("@nexusbot/lottery-mcp-core").LotteryMcpClient;
    server: McpServer;
    toolCatalog: LotteryToolDefinition[];
};
export declare const startLotteryMcpStdioServer: (options: LotteryMcpClientConfig) => Promise<{
    client: import("@nexusbot/lottery-mcp-core").LotteryMcpClient;
    server: McpServer;
    toolCatalog: LotteryToolDefinition[];
    transport: StdioServerTransport;
}>;
export declare const startNbcpStdioServer: (options: LotteryMcpClientConfig) => Promise<{
    client: import("@nexusbot/lottery-mcp-core").LotteryMcpClient;
    server: McpServer;
    toolCatalog: LotteryToolDefinition[];
    transport: StdioServerTransport;
}>;
export {};
