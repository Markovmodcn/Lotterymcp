export const LOTTERY_MCP_PROVIDER = 'remote';
export const LOTTERY_MCP_TOOLS = [
    'lottery.latest',
    'lottery.history',
    'lottery.periods',
    'lottery.summary',
];
export class McpApiError extends Error {
    statusCode;
    code;
    upgradeUrl;
    displayMode;
    action;
    data;
    constructor(input) {
        super(input.message);
        this.name = 'McpApiError';
        this.statusCode = input.statusCode;
        this.code = input.code;
        this.upgradeUrl = input.upgradeUrl;
        this.displayMode = input.displayMode;
        this.action = input.action;
        this.data = input.data;
    }
}
const DEFAULT_PERIODS = '100';
const RATE_LIMIT_RETRIES = 2;
const RATE_LIMIT_BASE_DELAY_MS = 1000;
const RATE_LIMIT_MAX_DELAY_MS = 5000;
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const getRateLimitDelayMs = (response, attempt) => {
    const retryAfter = response.headers.get('retry-after');
    if (retryAfter) {
        const parsed = Number(retryAfter);
        if (Number.isFinite(parsed) && parsed >= 0) {
            return Math.min(parsed * 1000, RATE_LIMIT_MAX_DELAY_MS);
        }
    }
    return Math.min(RATE_LIMIT_BASE_DELAY_MS * 2 ** Math.max(attempt - 1, 0), RATE_LIMIT_MAX_DELAY_MS);
};
export const normalizeApiBaseUrl = (value) => String(value || '')
    .trim()
    .replace(/\/+$/, '')
    .replace(/\/api\/v1\/mcp$/i, '')
    .replace(/\/api\/v1$/i, '')
    .replace(/\/api$/i, '');
const buildSearchParams = (query) => {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(query || {})) {
        if (value === undefined || value === null || value === '') {
            continue;
        }
        searchParams.set(key, String(value));
    }
    return searchParams;
};
const parseJsonSafely = (rawText) => {
    if (!rawText) {
        return {};
    }
    try {
        return JSON.parse(rawText);
    }
    catch {
        return {
            message: rawText,
        };
    }
};
const createApiError = (statusCode, payload) => new McpApiError({
    statusCode,
    message: String(payload?.message || '网站接口请求失败'),
    code: typeof payload?.code === 'string' ? payload.code : undefined,
    upgradeUrl: typeof payload?.upgradeUrl === 'string' ? payload.upgradeUrl : undefined,
    displayMode: typeof payload?.displayMode === 'string' ? payload.displayMode : undefined,
    action: payload?.action && typeof payload.action === 'object'
        ? payload.action
        : undefined,
    data: payload,
});
export const formatMcpApiError = (error) => {
    if (!(error instanceof McpApiError)) {
        return error instanceof Error ? error.message : String(error);
    }
    const lines = [error.message];
    if (error.statusCode === 429) {
        lines.push('建议先稍后重试，或降低默认期数/调用频率后再试。');
    }
    if (error.code) {
        lines.push(`错误代码: ${error.code}`);
    }
    if (error.action?.url) {
        lines.push(`处理链接: ${error.action.url}`);
    }
    else if (error.upgradeUrl) {
        lines.push(`升级页面: ${error.upgradeUrl}`);
    }
    return lines.join('\n');
};
export const createLotteryMcpClient = (config) => {
    const apiBaseUrl = normalizeApiBaseUrl(config.apiBaseUrl);
    const token = String(config.token || '').trim();
    const defaultPeriods = String(config.defaultPeriods || DEFAULT_PERIODS).trim() || DEFAULT_PERIODS;
    const fetchImpl = config.fetchImpl || fetch;
    const request = async (path, query) => {
        if (!apiBaseUrl) {
            throw new McpApiError({
                statusCode: 400,
                code: 'NBCP_CONFIG_MISSING_API_BASE_URL',
                message: '未配置 API_BASE_URL',
            });
        }
        const url = new URL(`/api/v1/mcp/${path.replace(/^\/+/, '')}`, `${apiBaseUrl}/`);
        url.search = buildSearchParams(query).toString();
        let response;
        for (let attempt = 1; attempt <= RATE_LIMIT_RETRIES + 1; attempt += 1) {
            try {
                response = await fetchImpl(url, {
                    method: 'GET',
                    headers: {
                        accept: 'application/json',
                        ...(token ? { 'x-api-key': token } : {}),
                    },
                });
            }
            catch (error) {
                throw new McpApiError({
                    statusCode: 503,
                    code: 'NBCP_NETWORK_ERROR',
                    message: error instanceof Error ? `无法连接网站接口: ${error.message}` : '无法连接网站接口',
                    data: error,
                });
            }
            if (response.status === 429 && attempt <= RATE_LIMIT_RETRIES) {
                await sleep(getRateLimitDelayMs(response, attempt));
                continue;
            }
            break;
        }
        if (!response) {
            throw new McpApiError({
                statusCode: 503,
                code: 'NBCP_NETWORK_ERROR',
                message: '无法连接网站接口',
            });
        }
        const rawText = await response.text();
        const payload = parseJsonSafely(rawText);
        if (!response.ok) {
            throw createApiError(response.status, payload);
        }
        return payload;
    };
    return {
        apiBaseUrl,
        token,
        defaultPeriods,
        getHealth: () => request('health'),
        getLatest: (query) => request('lottery/latest', query),
        getHistory: (query) => request('lottery/history', query),
        getPeriods: (query) => request('lottery/periods', query),
        getSummary: (query) => request('lottery/summary', query),
    };
};
export const createLotteryApiClient = createLotteryMcpClient;
