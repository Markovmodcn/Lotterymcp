export declare const LOTTERY_MCP_PROVIDER = "remote";
export declare const LOTTERY_MCP_TOOLS: readonly ["lottery.latest", "lottery.history", "lottery.periods", "lottery.summary"];
export type LotteryMcpToolName = (typeof LOTTERY_MCP_TOOLS)[number];
export type McpPlan = 'public' | 'member';
export type McpMeta = {
    plan: McpPlan;
    apiKeyUsed?: boolean;
    requestLimit: number | null;
    generatedAt: string;
    memberGroupId?: number | null;
    memberGroupName?: string | null;
    page?: number;
    limit?: number;
    total?: number;
    hasMore?: boolean;
};
export type McpEnvelope<T> = {
    data: T;
    meta: McpMeta;
};
export type McpHealthResponse = {
    ok: boolean;
    service: string;
    transport?: string;
    auth?: {
        header?: string;
    };
    tools?: string[];
};
export type LotteryLatestQuery = {
    lotteryType: string;
};
export type LotteryHistoryQuery = {
    lotteryType?: string;
    period?: string;
    fromDate?: string;
    toDate?: string;
    page?: number;
    limit?: number;
};
export type LotteryPeriodsQuery = {
    lotteryType: string;
    page?: number;
    limit?: number;
};
export type LotterySummaryQuery = {
    lotteryType?: string;
};
export type NbcpConfig = {
    apiBaseUrl: string;
    token: string;
    defaultPeriods: string;
};
export type LotteryMcpClientConfig = {
    apiBaseUrl: string;
    token?: string;
    defaultPeriods?: string;
    fetchImpl?: typeof fetch;
};
export type LotteryMcpClient = {
    apiBaseUrl: string;
    token: string;
    defaultPeriods: string;
    getHealth(): Promise<McpHealthResponse>;
    getLatest(query: LotteryLatestQuery): Promise<McpEnvelope<unknown>>;
    getHistory(query: LotteryHistoryQuery): Promise<McpEnvelope<unknown>>;
    getPeriods(query: LotteryPeriodsQuery): Promise<McpEnvelope<unknown>>;
    getSummary(query: LotterySummaryQuery): Promise<McpEnvelope<unknown>>;
};
export type McpAction = {
    type?: string;
    label?: string;
    url?: string;
};
export declare class McpApiError extends Error {
    readonly statusCode: number;
    readonly code?: string;
    readonly upgradeUrl?: string;
    readonly displayMode?: string;
    readonly action?: McpAction;
    readonly data?: unknown;
    constructor(input: {
        statusCode: number;
        message: string;
        code?: string;
        upgradeUrl?: string;
        displayMode?: string;
        action?: McpAction;
        data?: unknown;
    });
}
export declare const normalizeApiBaseUrl: (value: string) => string;
export declare const formatMcpApiError: (error: unknown) => string;
export declare const createLotteryMcpClient: (config: LotteryMcpClientConfig) => LotteryMcpClient;
export declare const createLotteryApiClient: (config: LotteryMcpClientConfig) => LotteryMcpClient;
